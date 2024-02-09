import datetime

from lxml import etree
from pydantic import BaseModel

from trafikkmeldinger.datex_api import get_situation_data, namespaces


class Situation(BaseModel):
    """Situation model."""

    type: str
    id: str
    updated_time: datetime.datetime
    record_id: str
    record_version: str
    record_version_time: datetime.datetime
    valid_from: datetime.datetime
    valid_to: datetime.datetime
    area: str
    location: str
    comment: str


def get_situations(type: str | None = None) -> list[Situation]:
    """Get situation."""
    xml = get_situation_data(type)
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)

    situations = []
    for situation in root.xpath("//ns12:situation", namespaces=namespaces):
        # Situation
        situation_id = situation.xpath("@id", namespaces=namespaces)[0]
        updated_time = situation.xpath(
            "./ns12:situationVersionTime", namespaces=namespaces
        )[0].text

        # Record
        extracted_type = ""
        if type:
            record = situation.xpath(
                f"./ns12:situationRecord[@xsi:type='ns12:{type}']",
                namespaces=namespaces,
            )[0]
        else:
            record = situation.xpath(
                "./ns12:situationRecord",
                namespaces=namespaces,
            )[0]
            extracted_type = record.xpath("@xsi:type", namespaces=namespaces)[0].split(
                ":"
            )[1]

        record_id = record.xpath("@id", namespaces=namespaces)[0]

        record_version = record.xpath("@version", namespaces=namespaces)[0]
        record_version_time = record.xpath(
            "./ns12:situationRecordVersionTime", namespaces=namespaces
        )[0].text
        valid_from = record.xpath(".//ns1:overallStartTime", namespaces=namespaces)[
            0
        ].text
        valid_to = record.xpath(".//ns1:overallEndTime", namespaces=namespaces)[0].text
        comment = record.xpath(
            ".//ns12:generalPublicComment//ns1:value[@lang='no']", namespaces=namespaces
        )[0].text
        location = record.xpath(
            ".//ns8:locationDescription//ns1:value[@lang='no']", namespaces=namespaces
        )[0].text
        area = record.xpath(
            ".//ns8:namedArea//ns1:value[@lang='no']", namespaces=namespaces
        )[0].text

        situations.append(
            Situation(
                type=type or extracted_type,
                id=situation_id,
                updated_time=updated_time,
                record_id=record_id,
                record_version=record_version,
                record_version_time=record_version_time,
                valid_from=valid_from,
                valid_to=valid_to,
                area=area,
                location=location,
                comment=comment,
            )
        )

    return situations
