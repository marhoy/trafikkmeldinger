import datetime
from typing import Dict, List, Union

from loguru import logger
from pydantic import parse_obj_as

from trafikkmeldinger.classes import Conversation, Tweet
from trafikkmeldinger.twitter_api import TwitterSession

session = TwitterSession(
    "twitter_cache",
    expire_after=datetime.timedelta(minutes=1),
    ignored_parameters=["start_time"],
)


def get_user_id(username: str) -> int:
    r = session.get(f"users/by/username/{username}")
    return int(r.json()["data"]["id"])


def get_tweets(username: str, past_hours: int) -> List[Tweet]:
    user_id = get_user_id(username)

    start_time = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        microsecond=0
    ) - datetime.timedelta(hours=past_hours)
    params: Dict[str, Union[int, str]] = {
        "max_results": 100,
        "start_time": start_time.isoformat(),
        # "end_time": (start_time + datetime.timedelta(hours=6)).isoformat(),
        "tweet.fields": "created_at,conversation_id",
        "exclude": "retweets",
    }
    r = session.get(f"users/{user_id}/tweets", params=params)
    if r.from_cache:
        logger.debug("Twitter API: Using cache")
    else:
        logger.debug("Twitter API: Got new data")

    tweets = parse_obj_as(List[Tweet], r.json()["data"])
    return tweets


def get_tweet_conversations(username: str, past_hours: int) -> List[Conversation]:
    """Get list of conversations, most recent first."""
    tweets = get_tweets(username, past_hours)
    conversations: Dict[int, Conversation] = dict()
    for tweet in reversed(tweets):
        if not conversations.get(tweet.conversation_id):
            conversations[tweet.conversation_id] = Conversation(tweet)
        else:
            conversations[tweet.conversation_id].add_tweet(tweet)

    return list(reversed(conversations.values()))
