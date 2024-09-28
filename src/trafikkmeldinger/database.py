"""Database module for trafikkmeldinger."""

from sqlmodel import SQLModel, create_engine

sqlite_url = "sqlite:///./trafikkmeldinger.db"
engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables() -> None:
    """Create the database and tables."""
    SQLModel.metadata.create_all(engine)
