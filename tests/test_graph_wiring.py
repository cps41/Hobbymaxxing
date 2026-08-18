import datetime as dt

import pytest

from hobbymaxxing.graph import build_graph


@pytest.fixture(autouse=True)
def mock_personal_system_apis(monkeypatch):
    """Graph wiring tests exercise routing/fan-out/fan-in shape, not real
    Calendar/weather integrations, so stub those out at the network boundary."""

    def fake_get_events(horizon="today"):
        return []

    monkeypatch.setattr("hobbymaxxing.integrations.calendar_api.get_events", fake_get_events)


def _mock_weather(monkeypatch, *, sunset: dt.datetime):
    def fake_get_current_weather():
        return {
            "temperature_c": 15.0,
            "precipitation_mm": 0.0,
            "weather_code": 0,
            "is_day": True,
            "precipitation_probability": 0.1,
            "sunset": sunset.isoformat(),
        }

    monkeypatch.setattr(
        "hobbymaxxing.integrations.weather.get_current_weather", fake_get_current_weather
    )


def test_graph_runs_end_to_end(monkeypatch):
    now = dt.datetime.now().astimezone()
    _mock_weather(monkeypatch, sunset=now + dt.timedelta(hours=3))

    graph = build_graph()
    result = graph.invoke({"run_timestamp": now.isoformat(), "horizon": "today"})

    assert "final_recommendation" in result
    assert result["final_recommendation"]["hobby"]


def test_router_skips_fly_fishing_when_dark(monkeypatch):
    now = dt.datetime.now().astimezone()
    _mock_weather(monkeypatch, sunset=now - dt.timedelta(hours=1))

    graph = build_graph()
    result = graph.invoke({"run_timestamp": now.isoformat(), "horizon": "today"})

    assert "fly_fishing" not in result["active_domains"]
    assert result.get("fly_fishing_suggestion") is None
    assert "fly_fishing" in result["skip_reasons"]
