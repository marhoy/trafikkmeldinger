import datetime
import importlib.resources

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from trafikkmeldinger import jinja_filters
from trafikkmeldinger.twitter_data import get_tweet_conversations

app = FastAPI()

with importlib.resources.path("trafikkmeldinger", "static") as static_dir:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

with importlib.resources.path("trafikkmeldinger", "templates") as template_dir:
    templates = Jinja2Templates(directory=template_dir)

# Add custom Jinja filters
templates.env.filters["timestamp_to_str"] = jinja_filters.timestamp_to_str
templates.env.filters["status_to_class"] = jinja_filters.status_to_class


class TweetRequest(BaseModel):
    username: str = "VTSost"
    past_hours: int = 24


@app.get("/", response_class=HTMLResponse)
async def main(
    request: Request,
    username: str = Query(default="VTSost", max_length=15),
    past_hours: int = Query(default=24, ge=1, le=48),
) -> Response:
    conversations = get_tweet_conversations(username, past_hours)
    last_tweet_timestamp = max(conv.updated_at for conv in conversations)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "updated_timestamp": datetime.datetime.now(),
            "last_tweet_timestamp": last_tweet_timestamp,
            "conversations": conversations,
        },
    )
