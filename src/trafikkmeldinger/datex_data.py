"""Module for fetching and parsing data from the Datex II API."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import Generator

from loguru import logger
from requests.exceptions import ConnectionError

from trafikkmeldinger.datex_api import get_situation_xml, namespaces
from trafikkmeldinger.sqlmodels import Record, RecordBase, Situation, SituationBase


def get_situations_with_records() -> Generator[Situation, None, None]:
    """Get situation data from the API and return a generator of Situation objects."""
    try:
        root = ET.fromstring(get_situation_xml())  # noqa: S314
    except (ConnectionError, ET.ParseError) as error:
        # If we can't connect to the server, or can't parse the data.
        logger.warning(f"Could not connect to the server or parse the data: {error}.")
        return

    for situation in root.iterfind(".//ns12:situation", namespaces=namespaces):
        # Get situation data
        situation_id = situation.get("id", default="")
        situation_version_time = datetime.fromisoformat(
            situation.findtext(
                "./ns12:situationVersionTime",
                default="",
                namespaces=namespaces,
            )
        )

        # Create situation data object. This will cause Pydantic to validate the data.
        situation_data = SituationBase(
            id=situation_id, version_time=situation_version_time
        )
        # Create situation db object, which doesn't trigger validation.
        situation_db = Situation.model_validate(situation_data)

        # Loop over records in the situation
        for record in situation.findall(
            "./ns12:situationRecord", namespaces=namespaces
        ):
            # Get record data
            record_id = record.get("id", default="")
            record_version = int(
                record.get(
                    "version",
                    default=0,
                )
            )
            record_type = record.get(f"{{{namespaces['xsi']}}}type", default="").split(
                ":"
            )[-1]
            record_versiontime = datetime.fromisoformat(
                record.findtext(
                    "./ns12:situationRecordVersionTime",
                    default="",
                    namespaces=namespaces,
                )
            )
            record_valid_from = datetime.fromisoformat(
                record.findtext(
                    ".//overallStartTime",
                    default="",
                    namespaces=namespaces,
                )
            )
            # If overallEndTime is missing, the record is valid until further notice.
            if record_valid_to_string := record.findtext(
                ".//overallEndTime",
                default="",
                namespaces=namespaces,
            ):
                record_valid_to = datetime.fromisoformat(record_valid_to_string)
            else:
                record_valid_to = datetime.now(UTC) + timedelta(days=365)
            record_area = record.findtext(
                ".//ns6:areaName//value[@lang='no']",
                default="",
                namespaces=namespaces,
            )
            record_location = record.findtext(
                ".//ns6:locationDescription//value[@lang='no']",
                default="",
                namespaces=namespaces,
            )
            record_comment = record.findtext(
                ".//ns12:generalPublicComment//value[@lang='no']",
                default="",
                namespaces=namespaces,
            )

            # Create record data object. This will cause Pydantic to validate the data.
            record_data = RecordBase(
                id=record_id,
                version=record_version,
                type=record_type,
                version_time=record_versiontime,
                valid_from=record_valid_from,
                valid_to=record_valid_to,
                area=record_area,
                location=record_location,
                comment=record_comment,
            )
            # Create record db object, which doesn't trigger validation.
            record_db = Record.model_validate(record_data)

            # Append record to current situation
            situation_db.records.append(record_db)

        # This feels broken, but when a model is defined with table=True, it is not
        # validated on creation. We need to manually validate the model.
        yield situation_db
