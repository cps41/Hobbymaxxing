import datetime as dt
import json
from unittest.mock import MagicMock

import pytest

from graph import build_graph


class _FakeLLM:
    """Stands in for config.get_llm(): inspects the prompt text to decide
    which node is calling (physical vs. restoration vs. synthesize) and
    returns a plausible JSON response for that node's parser, without any
    real API call."""

    def invoke(self, prompt: str):
        prompt_lower = prompt.lower()
        if "strength_training" in prompt_lower and "muay_thai" in prompt_lower:
            content = json.dumps(
                {"hobby": "walking", "confidence": 0.6, "reasoning": "fake LLM response for tests"}
            )
        elif "restoration" in prompt_lower and "gaming" in prompt_lower:
            content = json.dumps(
                {"hobby": "reading", "confidence": 0.7, "reasoning": "fake LLM response for tests"}
            )
        else:
            content = json.dumps(
                {
                    "hobby": "reading",
                    "reasoning": "fake synthesize response for tests",
                    "alternatives": ["strength_training", "coding"],
                }
            )
        return MagicMock(content=content)


@pytest.fixture(autouse=True)
def mock_personal_system_apis(monkeypatch):
    """Graph wiring tests exercise routing/fan-out/fan-in shape, not real
    Calendar/weather/Oura integrations or LLM calls, so stub those out at
    their respective boundaries."""

    def fake_get_events(horizon="today"):
        return []

    monkeypatch.setattr("hobbymaxxing.integrations.calendar_api.get_events", fake_get_events)
    monkeypatch.setattr("hobbymaxxing.integrations.oura.get_readiness", lambda: {"day": "2026-08-17", "score": 75, "contributors": {}})
    monkeypatch.setattr("hobbymaxxing.integrations.oura.get_sleep", lambda: {"day": "2026-08-17", "score": 80, "contributors": {}})
    monkeypatch.setattr("hobbymaxxing.integrations.oura.get_activity", lambda **kwargs: [])
    monkeypatch.setattr("hobbymaxxing.config.get_llm", lambda **kwargs: _FakeLLM())


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
