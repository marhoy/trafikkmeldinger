"""Define classes for trafikkmeldinger package."""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from enum import IntEnum

from pydantic import BaseModel


class Status(IntEnum):
    """Status of a thread."""

    NEW = 1
    FIXING = 2
    DONE = 3


class Message(BaseModel):
    """A message in a thread."""

    created_at: datetime.datetime
    text: str

    def __lt__(self, other: Message) -> bool:
        """Messages can be sorted by creation time."""
        return self.created_at < other.created_at


class Thread(ABC):
    """A thread of messages."""

    @property
    @abstractmethod
    def created_at(self) -> datetime.datetime:
        """The creation time of the thread."""
        pass

    @property
    @abstractmethod
    def status(self) -> Status:
        """The status of the thread."""
        pass

    @property
    @abstractmethod
    def location(self) -> str:
        """The location of the thread."""
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime.datetime:
        """The last update time of the thread."""
        pass

    @property
    @abstractmethod
    def messages(self) -> list[Message]:
        """The messages in the thread."""
        pass

    def __lt__(self, other: Thread) -> bool:
        """Threads can be sorted by creation time."""
        return self.created_at < other.created_at
