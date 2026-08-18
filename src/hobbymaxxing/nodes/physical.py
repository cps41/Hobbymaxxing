import datetime as dt
from typing import Any

from hobbymaxxing import config, llm_utils
from hobbymaxxing.integrations import oura
from hobbymaxxing.state import State, SubAgentSuggestion

_HIGH_ACTIVITY_MINUTES_THRESHOLD = 20  # a day counts as "high intensity" above this


def _days_since_high_activity(activity: list[dict[str, Any]]) -> int | None:
    today = dt.date.today()
    for record in reversed(activity):
        if record["high_activity_time"] / 60 >= _HIGH_ACTIVITY_MINUTES_THRESHOLD:
            return (today - dt.date.fromisoformat(record["day"])).days
    return None


def _assess_fatigue(
    readiness: dict[str, Any] | None,
    sleep: dict[str, Any] | None,
    activity: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "readiness_score": readiness["score"] if readiness else None,
        "sleep_score": sleep["score"] if sleep else None,
        "days_since_high_activity": _days_since_high_activity(activity),
    }


def physical(state: State) -> dict:
    readiness = oura.get_readiness()
    sleep = oura.get_sleep()
    activity = oura.get_activity()
    fatigue_assessment = _assess_fatigue(readiness, sleep, activity)

    prompt = llm_utils.load_prompt(
        "physical",
        time_of_day=state.get("current_time_context", {}).get("time_of_day", "unknown"),
        available_windows=state.get("available_windows", []),
        feeling=state.get("user_feeling_input") or "not specified",
        readiness_score=fatigue_assessment["readiness_score"],
        sleep_score=fatigue_assessment["sleep_score"],
        recent_activity=activity,
        days_since_high_activity=fatigue_assessment["days_since_high_activity"],
        recent_history=state.get("recent_run_history", []),
    )

    response = config.get_llm().invoke(prompt)
    parsed = llm_utils.parse_json_response(response.content)

    suggestion: SubAgentSuggestion = {
        "hobby": parsed["hobby"],
        "confidence": float(parsed["confidence"]),
        "reasoning": parsed["reasoning"],
        "metadata": {},
    }
    return {
        "oura_readiness": readiness,
        "oura_sleep": sleep,
        "oura_activity": activity,
        "fatigue_assessment": fatigue_assessment,
        "physical_suggestion": suggestion,
    }
