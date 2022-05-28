import datetime
import zoneinfo

from trafikkmeldinger.classes import Status


def timestamp_to_str(
    timestamp: datetime.datetime, local_tz: str = "Europe/Oslo"
) -> str:
    """Format a timestamp."""
    date_diff = (
        timestamp.date() - datetime.datetime.now(tz=datetime.timezone.utc).date()
    )
    match date_diff.days:
        case 0:
            days_ago = ""
        case -1:  # noqa: E225
            days_ago = "I går "
        case _:
            days_ago = f"{-date_diff.days} dager siden "

    timestamp = timestamp.astimezone(zoneinfo.ZoneInfo(local_tz))
    return f"{days_ago}{timestamp:%H:%M}"


def status_to_class(status: Status) -> str:
    mapping = {
        Status.NEW: "list-group-item-danger",
        Status.FIXING: "list-group-item-warning",
        Status.DONE: "list-group-item-success",
    }
    return mapping[status]
