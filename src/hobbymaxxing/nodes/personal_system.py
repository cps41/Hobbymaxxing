from hobbymaxxing.state import State


def personal_system_check(state: State) -> dict:
    """Stub v1: hardcoded context, no real Calendar/weather calls yet (milestone 2)."""
    return {
        "calendar_events": [],
        "available_windows": [{"start": "18:00", "end": "21:00"}],
        "current_time_context": {"time_of_day": "evening", "is_dark": True},
        "weather_current": {"condition": "clear", "precipitation_probability": 0.1},
        "recent_run_history": [],
    }
