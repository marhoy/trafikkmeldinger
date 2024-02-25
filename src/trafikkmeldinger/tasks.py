from datetime import datetime, timedelta

from loguru import logger
from sqlmodel import Session, select

from trafikkmeldinger.database import create_db_and_tables, engine
from trafikkmeldinger.datex_data import get_situations_with_records
from trafikkmeldinger.sqlmodels import Record, Situation

create_db_and_tables()


def update_db_with_data() -> list[str]:
    current_situation_ids: list[str] = []

    with Session(engine) as session:
        num_updated, num_added = 0, 0
        for situation in get_situations_with_records():
            # Add this situation to the list of current situations
            current_situation_ids.append(situation.id)

            # Situation already exists in database
            if db_situation := session.exec(
                select(Situation).where(Situation.id == situation.id)
            ).one_or_none():
                # Update the version time
                db_situation.version_time = situation.version_time

                # Find existing records for this situation
                db_record_versions = session.exec(
                    select(Record.id, Record.version)
                    .join(Situation)
                    .where(Situation.id == situation.id)
                ).all()

                # Append any new records to situation
                for record in situation.records:
                    if (record.id, record.version) not in db_record_versions:
                        db_situation.records.append(record)

                # Add the updated situation to the session
                num_updated += 1
                session.add(db_situation)
                session.commit()
            else:
                # Situation does not exist in database
                num_added += 1
                session.add(situation)
                session.commit()

        logger.info(
            f"Updated {num_updated} situations and added {num_added} new situations."
        )
    return current_situation_ids


def mark_old_situations_inactive(current_situation_ids: list[str]) -> None:
    with Session(engine) as session:
        situations = session.exec(select(Situation))
        counter = 0
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
            .where(Situation.is_active is False)
            .where(Situation.version_time < datetime.now() - timedelta(days=7))
        ).all()

        # Delete all old situations
        logger.debug(f"Deleting {len(old_situations)} expired situations.")
        for situation in old_situations:
            session.delete(situation)

        # Commit all changes
        session.commit()


def scheduled_job() -> None:
    logger.info("Updating database")
    situation_ids = update_db_with_data()
    mark_old_situations_inactive(situation_ids)
    delete_old_situations()
    logger.info("Database updated")
