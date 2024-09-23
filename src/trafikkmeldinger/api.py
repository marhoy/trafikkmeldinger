"""Web server for displaying traffic messages."""

import datetime
from importlib.resources import as_file, files

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel
from zoneinfo import ZoneInfo

from trafikkmeldinger import jinja_filters
from trafikkmeldinger.politi_loggen import PoliceLog
from trafikkmeldinger.twitter_data import get_tweet_conversations

app = FastAPI()

with as_file(files("trafikkmeldinger").joinpath("static")) as static_dir:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

with as_file(files("trafikkmeldinger").joinpath("templates")) as template_dir:
    logger.warning(f"Template dir: {template_dir}")
    templates = Jinja2Templates(directory=template_dir)

# Add custom Jinja filters
templates.env.filters["timestamp_to_str"] = jinja_filters.timestamp_to_str
templates.env.filters["status_to_class"] = jinja_filters.status_to_class


class TweetRequest(BaseModel):
    """Incoming request model."""

    username: str = "VTSost"
    past_hours: int = 24


@app.get("/", response_class=HTMLResponse)
async def main(
    request: Request,
    username: str = Query(default="VTSost", max_length=15),
    past_hours: int = Query(default=24, ge=1, le=48),
) -> Response:
    """Generate html page with messages."""
    twitter_threads = get_tweet_conversations(username, past_hours)
    police_threads = PoliceLog().get_threads()
    threads = sorted(twitter_threads + police_threads, reverse=True)
    last_timestamp = max(thread.updated_at for thread in threads)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "updated_timestamp": datetime.datetime.now(tz=ZoneInfo("Europe/Oslo")),
            "last_tweet_timestamp": last_timestamp,
            "conversations": threads,
        },
    )
