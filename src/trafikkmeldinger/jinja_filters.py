"""Heler functions for Jinja2 templates."""

import datetime

import zoneinfo

from trafikkmeldinger.classes import Status


def timestamp_to_str(
    timestamp: datetime.datetime, local_tz: str = "Europe/Oslo"
) -> str:
    """Format a timestamp."""
    timestamp = timestamp.astimezone(zoneinfo.ZoneInfo(local_tz))
    date_diff = (
        timestamp.date() - datetime.datetime.now(tz=zoneinfo.ZoneInfo(local_tz)).date()
    )
    match date_diff.days:
        case 0:
            days_ago = ""
        case -1:
            days_ago = "I går "
        case _:
            days_ago = f"{-date_diff.days} dager siden "

    return f"{days_ago}{timestamp:%H:%M}"


def status_to_class(status: Status) -> str:
    """Map status to CSS class."""
    mapping = {
        Status.NEW: "list-group-item-danger",
        Status.FIXING: "list-group-item-warning",
        Status.DONE: "list-group-item-success",
    }
    return mapping[status]
