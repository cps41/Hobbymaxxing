import datetime as dt
from typing import Any

import requests

from hobbymaxxing import config

_BASE_URL = "https://api.ouraring.com/v2/usercollection"


def _get(endpoint: str, *, days_back: int = 7) -> list[dict[str, Any]]:
    if not config.OURA_PERSONAL_ACCESS_TOKEN:
        raise RuntimeError("OURA_PERSONAL_ACCESS_TOKEN must be set in .env to fetch Oura data")

    today = dt.date.today()
    response = requests.get(
        f"{_BASE_URL}/{endpoint}",
        headers={"Authorization": f"Bearer {config.OURA_PERSONAL_ACCESS_TOKEN}"},
        params={
            "start_date": (today - dt.timedelta(days=days_back)).isoformat(),
            "end_date": today.isoformat(),
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_readiness() -> dict[str, Any] | None:
    """Most recent daily readiness score + contributors, or None if no data yet today."""
    records = _get("daily_readiness")
    if not records:
        return None
    latest = records[-1]
    return {"day": latest["day"], "score": latest["score"], "contributors": latest["contributors"]}


def get_sleep() -> dict[str, Any] | None:
    records = _get("daily_sleep")
    if not records:
        return None
    latest = records[-1]
    return {"day": latest["day"], "score": latest["score"], "contributors": latest["contributors"]}


def get_activity(*, days_back: int = 7) -> list[dict[str, Any]]:
    """Last N days of activity, used for load/recency assessment rather than just today."""
    records = _get("daily_activity", days_back=days_back)
    return [
        {
            "day": r["day"],
            "score": r["score"],
            "active_calories": r["active_calories"],
            "steps": r["steps"],
            "high_activity_time": r["high_activity_time"],
        }
        for r in records
    ]
