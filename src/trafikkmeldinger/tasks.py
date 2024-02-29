from datetime import datetime, timedelta

from loguru import logger
from sqlmodel import Integer, Session, cast, func, select

from trafikkmeldinger.database import create_db_and_tables, engine
from trafikkmeldinger.datex_data import get_situations_with_records
from trafikkmeldinger.sqlmodels import Record, Situation

create_db_and_tables()


def update_db_with_data() -> set[str]:
    current_situation_ids: set[str] = set()
    num_updated_time, num_added_records, num_added_situations = 0, 0, 0

    with Session(engine) as session:
        for situation in get_situations_with_records():
            # Add this situation to the list of current situations
            current_situation_ids.add(situation.id)

            # Situation already exists in database
            if db_situation := session.exec(
                select(Situation).where(Situation.id == situation.id)
            ).one_or_none():
                # Update the version time
                if db_situation.version_time < situation.version_time:
                    num_updated_time += 1
                    db_situation.version_time = situation.version_time

                # Find existing records for this situation
                db_record_versions = [
                    (record.id, record.version) for record in db_situation.records
                ]

                # Append any new records to situation
                for record in situation.records:
                    if (record.id, record.version) not in db_record_versions:
                        # We need to create new Record objects: The ones in the
                        # "sitation" object are connected to the "situation" object, and
                        # would cause the new "situation" object to be added as well.
                        num_added_records += 1
                        db_situation.records.append(
                            Record.model_validate(record.model_dump())
                        )

                # Add the updated situation to the session
                session.add(db_situation)
            else:
                # Situation does not exist in database
                num_added_situations += 1
                session.add(situation)

        # Commit all changes
        session.commit()

        logger.debug(
            f"Added {num_added_situations} new situations, "
            f"updated {num_updated_time} timestamps and "
            f"added {num_added_records} new records."
        )
    return current_situation_ids


def mark_old_situations_inactive(current_situation_ids: set[str]) -> None:
    with Session(engine) as session:
        counter = 0
        situations = session.exec(select(Situation).where(Situation.is_active))
        for situation in situations:
            # Mark all old situations as inactive
            if situation.id not in current_situation_ids:
                counter += 1
                situation.is_active = False
                session.add(situation)

        # Commit all changes
        session.commit()
    logger.debug(f"Marked {counter} situation(s) as inactive.")


def delete_old_situations() -> None:
    with Session(engine) as session:
        # Find all situations that are not active
        old_situations = session.exec(
            select(Situation)
            .where(not Situation.is_active)
            .where(Situation.version_time < datetime.now() - timedelta(days=7))
        ).all()

        # Delete all old situations
        logger.debug(f"Deleting {len(old_situations)} expired situations.")
        for situation in old_situations:
            session.delete(situation)

        # Commit all changes
        session.commit()


def num_situations_and_records() -> tuple[int, int, int]:
    with Session(engine) as session:
        # Get the number of inactive and active situations
        results = session.exec(
            select(func.count(), Situation.is_active).group_by(
                cast(Situation.is_active, Integer)
            )
        )
        num_inactive_situations, num_active_situations = 0, 0
        for num, value in results:
            if value:
                num_active_situations = num
            else:
                num_inactive_situations = num

        # Get number of records
        num_records = session.exec(select(func.count()).select_from(Record)).one()
    return num_inactive_situations, num_active_situations, num_records


def scheduled_job() -> None:
    num_inactive_situations, num_active_situations, num_records = (
        num_situations_and_records()
    )
    logger.info(
        f"Updating database with {num_inactive_situations + num_active_situations} "
        f"situations ({num_active_situations} active) and {num_records} records."
    )
    situation_ids = update_db_with_data()
    mark_old_situations_inactive(situation_ids)
    delete_old_situations()
    logger.info("Done updating.")
