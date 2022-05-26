import datetime
from typing import Dict, List, Union

from pydantic import parse_obj_as

from trafikkmeldinger.schemas import Tweet
from trafikkmeldinger.twitter_api_session import TwitterSession

session = TwitterSession()
r = session.get("users/by/username/VTSost")
user_id = r.json()["data"]["id"]

# Get tweets up to 24 hours old
start_time = datetime.datetime.now(tz=datetime.timezone.utc).replace(
    microsecond=0
) - datetime.timedelta(hours=24)
params: Dict[str, Union[int, str]] = {
    "max_results": 100,
    "start_time": start_time.isoformat(),
    "tweet.fields": "created_at,conversation_id",
    "exclude": "retweets",
}
r = session.get(f"users/{user_id}/tweets", params=params)
tweets = parse_obj_as(List[Tweet], r.json()["data"])
