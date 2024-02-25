import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Generator

from trafikkmeldinger.datex_api import get_situation_xml, namespaces
from trafikkmeldinger.sqlmodels import Record, Situation


def get_situations_with_records() -> Generator[Situation, None, None]:
    root = ET.fromstring(get_situation_xml())
    for situation in root.iterfind(".//ns12:situation", namespaces=namespaces):

        # Get situation data
        situation_id = situation.get("id")
        situation_version_time = datetime.fromisoformat(
            situation.findtext(
                "./ns12:situationVersionTime",
                default="",
                namespaces=namespaces,
            )
        )

        # Create situation object
        situation_obj = Situation(id=situation_id, version_time=situation_version_time)

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
            record_valid_to = datetime.fromisoformat(
                record.findtext(
                    ".//overallEndTime",
                    default="",
                    namespaces=namespaces,
                )
            )
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

            # Create record object
            record_obj = Record(
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
            # Append record to current situation
            situation_obj.records.append(record_obj)
        yield situation_obj
