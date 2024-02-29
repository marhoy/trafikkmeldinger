from datetime import datetime, timezone
from typing import ClassVar, Optional

from pydantic import AfterValidator
from sqlalchemy import Label
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import Field, Relationship, SQLModel, func, select
from typing_extensions import Annotated


def make_datetime_naive(dt: datetime) -> datetime:
    """Convert a datetime object with timezone info to a naive datetime object."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


NaiveUTCDatetime = Annotated[datetime, AfterValidator(make_datetime_naive)]

# Store with timezone in database
#   last_login: datetime.datetime = sqlmodel.Field(
#       sa_column=sqlmodel.Column(
#           sqlmodel.DateTime(timezone=True),
#           nullable=False
#       ))


class SituationBase(SQLModel):
    """The situation data model."""

    id: str = Field(primary_key=True)
    version_time: NaiveUTCDatetime
    is_active: bool = True


class Situation(SituationBase, table=True):  # type: ignore
    """The situation table model."""

    def _num_records(self) -> int:
        return len(self.records)

    @classmethod
    def _num_records_expression(cls) -> Label[int]:
        return (
            select(func.count()).where(Record.situation_id == cls.id).label("whatever")
        )

    records: list["Record"] = Relationship(back_populates="situation")
    num_records: ClassVar[hybrid_property[int]] = hybrid_property(
        fget=_num_records, expr=_num_records_expression
    )


class RecordBase(SQLModel):
    """The record data model."""

    id: str
    version: int
    type: str
    version_time: NaiveUTCDatetime
    valid_from: NaiveUTCDatetime
    valid_to: NaiveUTCDatetime
    area: str
    location: str
    comment: str
    situation_id: str | None = Field(
        default=None, foreign_key="situation.id", nullable=False
    )


class Record(RecordBase, table=True):  # type: ignore
    """The record table model."""

    pkey: Optional[int] = Field(default=None, primary_key=True)
    situation: Situation = Relationship(back_populates="records")
