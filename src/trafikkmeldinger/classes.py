import datetime
import re
from enum import IntEnum
from os.path import commonprefix
from typing import List

from pydantic import BaseModel


class Status(IntEnum):
    NEW = 1
    FIXING = 2
    DONE = 3


class Tweet(BaseModel):
    id: int
    conversation_id: int
    created_at: datetime.datetime
    text: str


class Message(BaseModel):
    created_at: datetime.datetime
    text: str


def upperfirst(string: str) -> str:
    """Uppercase first character of string, leave rest unchanged."""
    return string[:1].upper() + string[1:]


class Conversation:
    def __init__(self, tweet: Tweet) -> None:
        self.created_at = tweet.created_at
        self.updated_at = tweet.created_at
        self.tweets: List[Tweet] = [tweet]
        self.status = Status.NEW
        self.location = ""
        self.messages: List[Message] = []
        self.update()

    def add_tweet(self, tweet: Tweet) -> None:
        self.updated_at = tweet.created_at
        self.tweets.append(tweet)
        self.update()

    def update(self) -> None:
        self.update_status()
        self.update_location_and_messages()

    def update_status(self) -> None:
        for tweet in self.tweets:
            if any(word in tweet.text.lower() for word in ("på stedet", "berging")):
                self.status = Status.FIXING
            if any(
                word in tweet.text.lower()
                for word in ("åpen", "åpnet", "fjernet", "ryddet", "sjekket")
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
            if match := re.match(r"(.+[.,:;])", prefix):
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
