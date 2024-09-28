"""Get data from Twitter API."""

from __future__ import annotations

import datetime
import re
from os.path import commonprefix
from typing import List

from loguru import logger
from pydantic import TypeAdapter

from trafikkmeldinger.classes import Message, Status, Thread
from trafikkmeldinger.twitter_api import TwitterSession

session = TwitterSession(
    "twitter_cache",
    expire_after=datetime.timedelta(minutes=1),
    ignored_parameters=["start_time"],
)


class Tweet(Message):
    """A tweet from Twitter / X."""

    id: int
    conversation_id: int


def upperfirst(string: str) -> str:
    """Uppercase first character of string, leave rest unchanged."""
    return string[:1].upper() + string[1:]


class TwitterThread(Thread):
    """A thread consisting of multiple messages."""

    def __init__(self, tweet: Tweet) -> None:
        """Initialize a thread with a message."""
        self._tweets: list[Tweet] = [tweet]

    def add_tweet(self, tweet: Tweet) -> None:
        """Add a tweet to the conversation."""
        self._tweets.append(tweet)

    @property
    def created_at(self) -> datetime.datetime:
        """The creation time of the thread."""
        return min(tweet.created_at for tweet in self._tweets)

    @property
    def updated_at(self) -> datetime.datetime:
        """The last update time of the thread."""
        return max(tweet.created_at for tweet in self._tweets)

    @property
    def status(self) -> Status:
        """The status of the thread."""
        status = Status.NEW
        for tweet in self._tweets:
            if any(word in tweet.text.lower() for word in ("på stedet", "berging")):
                status = Status.FIXING
            if any(
                word in tweet.text.lower()
                for word in ("åpen", "åpnet", "åpne", "fjernet", "ryddet", "sjekket")
            ):
                status = Status.DONE
        return status

    @property
    def location(self) -> str:
        """The location of the thread."""
        tweet_prefix = self._tweet_prefix()
        return tweet_prefix.rstrip(" ,:;.").replace("#", "")

    @property
    def messages(self) -> list[Message]:
        """Create messages from Tweets."""
        tweet_prefix = self._tweet_prefix()
        messages = [
            Message(
                text=upperfirst(tweet.text.removeprefix(tweet_prefix).lstrip(" ,:;.")),
                created_at=tweet.created_at,
            )
            for tweet in self._tweets
        ]
        return sorted(messages)

    def _tweet_prefix(self) -> str:
        """Get the common prefix of the tweets."""
        if len(self._tweets) == 1:
            # If there is only one tweet, assume location is the first substring that
            # ends with either of .:; (and then something else than a number, to avoid
            # splitting on 'Rv. 3')
            if match := re.match(r"^(.+?)[.:;]\s+\D", self._tweets[0].text):
                prefix = match.group(1)
            else:
                prefix = ""
        else:
            # If there are multiple tweets, assume the common prefix is the location.
            prefix = commonprefix([tweet.text for tweet in self._tweets])
            if match := re.match(r"^(.+?)[.:;]\s+\D", prefix):
                # Include up to the last ,.:;
                prefix = match.group(1)

        return prefix


def get_user_id(username: str) -> int:
    """Get user ID from username."""
    r = session.get(f"users/by/username/{username}")
    return int(r.json()["data"]["id"])


def get_tweets(username: str, past_hours: int) -> list[Tweet]:
    """Get tweets from a user."""
    user_id = get_user_id(username)

    start_time = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        microsecond=0
    ) - datetime.timedelta(hours=past_hours)
    params: dict[str, int | str] = {
        "max_results": 100,
        "start_time": start_time.isoformat(),
        # "end_time": (start_time + datetime.timedelta(hours=6)).isoformat(),
        "tweet.fields": "created_at,conversation_id",
        "exclude": "retweets",
    }
    r = session.get(f"users/{user_id}/tweets", params=params)
    list_tweet_adapter = TypeAdapter(List[Tweet])
    tweets = list_tweet_adapter.validate_python(r.json()["data"])
    if r.from_cache:
        logger.debug(f"Twitter API: Using cached response ({len(tweets)} tweets).")
    else:
        logger.debug(f"Twitter API: Got new data ({len(tweets)} tweets).")

    return tweets


def get_tweet_conversations(username: str, past_hours: int) -> list[TwitterThread]:
    """Get list of conversations, most recent first."""
    tweets = get_tweets(username, past_hours)
    conversations: dict[int, TwitterThread] = {}
    for tweet in reversed(tweets):
        if not conversations.get(tweet.conversation_id):
            conversations[tweet.conversation_id] = TwitterThread(tweet)
        else:
            conversations[tweet.conversation_id].add_tweet(tweet)

    return list(reversed(conversations.values()))
