import datetime
import importlib.resources

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


@app.get("/", response_class=HTMLResponse)
async def main(request: Request) -> Response:
    conversations = get_tweet_conversations("VTSost", 24)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "update_timestamp": datetime.datetime.now(),
            "conversations": conversations,
        },
    )
