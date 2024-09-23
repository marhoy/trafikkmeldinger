"""Get messages from the police log."""

from __future__ import annotations

import datetime

import requests_cache
from pydantic import Field

from trafikkmeldinger.classes import Message, Status, Thread


class PoliceMessage(Message):
    """A message in the police log."""

    id: str
    thread_id: str = Field(alias="threadId")
    district: str
    municipality: str
    area: str
    is_active: bool = Field(alias="isActive")
    created_at: datetime.datetime = Field(alias="createdOn")

    @property
    def location(self) -> str:
        """Return the location of the message."""
        if self.area:
            return f"{self.municipality}: {self.area}"
        return f"{self.municipality}"


class PoliceThread(Thread):
    """A thread of messages from the police log."""

    def __init__(self, message: PoliceMessage) -> None:
        """Initialize class object."""
        self._messages = [message]

    @property
    def created_at(self) -> datetime.datetime:
        """Return the creation time of the thread."""
        return min(message.created_at for message in self._messages)

    @property
    def updated_at(self) -> datetime.datetime:
        """Return the last update time of the thread."""
        return max(message.created_at for message in self._messages)

    @property
    def status(self) -> Status:
        """Return the status of the thread."""
        if self._messages[-1].is_active:
            return Status.NEW
        return Status.DONE

    @property
    def location(self) -> str:
        """Return the location of the thread."""
        return self._messages[0].location

    @property
    def messages(self) -> list[Message]:
        """Return the messages in the thread."""
        messages = [
            Message.model_validate(message.model_dump()) for message in self._messages
        ]
        return sorted(messages)

    def _add_message(self, message: PoliceMessage) -> None:
        """Add a message to the thread."""
        self._messages.append(message)


class PoliceLog:
    """Get messages from the police log."""

    def __init__(self) -> None:
        """Initialize class object."""
        self.base_url = "https://api.politiet.no/politiloggen/v1"
        self.session = requests_cache.CachedSession(
            "politi_cache",
            expire_after=datetime.timedelta(minutes=2),
        )

    def get_threads(self) -> list[Thread]:
        """Get threads from the police log."""
        params = {
            "Districts": ["Oslo"],
            "Categories": ["Trafikk"],
            "Take": 50,
        }
        with self.session as session:
            r = session.get(f"{self.base_url}/messages", params=params, timeout=10)
        r.raise_for_status()
        threads: dict[str, PoliceThread] = {}
        for item in r.json().get("data", []):
            message = PoliceMessage(**item)
            if message.thread_id not in threads:
                threads[message.thread_id] = PoliceThread(message)
            else:
                threads[message.thread_id]._add_message(message)
        return list(threads.values())
