from typing import Any

import requests

from hobbymaxxing import config

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_current_weather() -> dict[str, Any]:
    """Fetch current conditions + today's precipitation/sunset from Open-Meteo."""
    if not config.HOME_LAT or not config.HOME_LON:
        raise RuntimeError("HOME_LAT/HOME_LON must be set in .env to fetch weather")

    response = requests.get(
        _FORECAST_URL,
        params={
            "latitude": config.HOME_LAT,
            "longitude": config.HOME_LON,
            "current": "temperature_2m,precipitation,weather_code,is_day",
            "daily": "precipitation_probability_max,sunset",
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    current = data["current"]
    daily = data["daily"]

    return {
        "temperature_c": current["temperature_2m"],
        "precipitation_mm": current["precipitation"],
        "weather_code": current["weather_code"],
        "is_day": bool(current["is_day"]),
        "precipitation_probability": daily["precipitation_probability_max"][0] / 100.0,
        "sunset": daily["sunset"][0],
    }
