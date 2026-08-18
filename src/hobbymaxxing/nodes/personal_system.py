import datetime as dt
from typing import Any

from hobbymaxxing.integrations import calendar_api, weather
from hobbymaxxing.state import State

_DAY_END_HOUR = 22  # latest hour we consider "available" for a hobby


def _parse_event_bounds(event: dict[str, Any]) -> tuple[dt.datetime, dt.datetime] | None:
    """All-day events use a date-only string with no time component; skip those
    for free-time-window purposes since they don't block a specific time slot."""
    try:
        start = dt.datetime.fromisoformat(event["start"])
        end = dt.datetime.fromisoformat(event["end"])
    except ValueError:
        return None
    return start, end


def _available_windows(events: list[dict[str, Any]], now: dt.datetime) -> list[dict[str, str]]:
    day_end = now.replace(hour=_DAY_END_HOUR, minute=0, second=0, microsecond=0)
    if day_end <= now:
        return []

    busy = sorted(
        (bounds for e in events if (bounds := _parse_event_bounds(e)) is not None),
        key=lambda b: b[0],
    )

    windows = []
    cursor = now
    for start, end in busy:
        if start >= day_end:
            break
        if start > cursor:
            windows.append((cursor, min(start, day_end)))
        cursor = max(cursor, end)
    if cursor < day_end:
        windows.append((cursor, day_end))

    return [
        {"start": w_start.isoformat(), "end": w_end.isoformat()}
        for w_start, w_end in windows
        if w_end > w_start
    ]


def personal_system_check(state: State) -> dict:
    now = dt.datetime.now().astimezone()
    horizon = state.get("horizon", "today")

    calendar_events = calendar_api.get_events(horizon=horizon)
    weather_current = weather.get_current_weather()

    sunset = dt.datetime.fromisoformat(weather_current["sunset"])
    is_dark = now >= sunset

    return {
        "calendar_events": calendar_events,
        "available_windows": _available_windows(calendar_events, now),
        "current_time_context": {
            "time_of_day": now.strftime("%H:%M"),
            "is_dark": is_dark,
        },
        "weather_current": weather_current,
        "recent_run_history": [],  # wired up in milestone 7 (persistence)
    }
