"""Define classes for trafikkmeldinger package."""

import datetime
import re
from enum import IntEnum
from os.path import commonprefix

from pydantic import BaseModel


class Status(IntEnum):
    """Status of a conversation."""

    NEW = 1
    FIXING = 2
    DONE = 3


class Tweet(BaseModel):
    """A tweet from Twitter / X."""

    id: int
    conversation_id: int
    created_at: datetime.datetime
    text: str


class Message(BaseModel):
    """A message in a conversation."""

    created_at: datetime.datetime
    text: str


def upperfirst(string: str) -> str:
    """Uppercase first character of string, leave rest unchanged."""
    return string[:1].upper() + string[1:]


class Conversation:
    """A conversation consisting of multiple messages."""

    def __init__(self, tweet: Tweet) -> None:
        """Initialize a conversation with a tweet."""
        self.created_at = tweet.created_at
        self.updated_at = tweet.created_at
        self.tweets: list[Tweet] = [tweet]
        self.status = Status.NEW
        self.location = ""
        self.messages: list[Message] = []
        self.update()

    def add_tweet(self, tweet: Tweet) -> None:
        """Add a tweet to the conversation."""
        self.updated_at = tweet.created_at
        self.tweets.append(tweet)
        self.update()

    def update(self) -> None:
        """Update status, location and messages."""
        self.update_status()
        self.update_location_and_messages()

    def update_status(self) -> None:
        """Update conversation status based on tweets."""
        for tweet in self.tweets:
            if any(word in tweet.text.lower() for word in ("på stedet", "berging")):
                self.status = Status.FIXING
            if any(
                word in tweet.text.lower()
                for word in ("åpen", "åpnet", "åpne", "fjernet", "ryddet", "sjekket")
            ):
                self.status = Status.DONE

    def update_location_and_messages(self) -> None:
        """Exctract location string from messages and remove it from all messages."""
        if len(self.tweets) == 1:
            # If there is only one tweet, assume location is the first substring that
            # ends with either of .:; (and then something else than a number, to avoid
            # splitting on 'Rv. 3')
            if match := re.match(r"^(.+?)[.:;]\s+\D", self.tweets[0].text):
                prefix = match.group(1)
            else:
                prefix = ""
        else:
            # If there are multiple tweets, assume the common prefix is the location.
            prefix = commonprefix([tweet.text for tweet in self.tweets])
            if match := re.match(r"^(.+?)[.:;]\s+\D", prefix):
                # Include up to the last ,.:;
                prefix = match.group(1)

        self.location = prefix.rstrip(" ,:;.").replace("#", "")
        self.messages = [
            Message(
                text=upperfirst(tweet.text.removeprefix(prefix).lstrip(" ,:;.")),
                created_at=tweet.created_at,
            )
            for tweet in self.tweets
        ]
