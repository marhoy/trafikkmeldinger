from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class Situation(SQLModel, table=True):  # type: ignore
    id: str = Field(primary_key=True)
    version_time: datetime
    is_active: bool = True
    records: list["Record"] = Relationship(back_populates="situation")


class Record(SQLModel, table=True):  # type: ignore
    pkey: int | None = Field(default=None, primary_key=True)
    situation_id: str | None = Field(
        default=None, foreign_key="situation.id", nullable=False
    )
    situation: Situation = Relationship(back_populates="records")
    id: str
    version: int
    type: str
    version_time: datetime
    valid_from: datetime
    valid_to: datetime
    area: str
    location: str
    comment: str
