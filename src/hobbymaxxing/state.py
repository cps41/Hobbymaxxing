from typing import Any, TypedDict


class SubAgentSuggestion(TypedDict):
    hobby: str
    confidence: float
    reasoning: str
    metadata: dict[str, Any]


class State(TypedDict, total=False):
    # run-level input
    run_timestamp: str
    horizon: str  # "today" | "week"
    user_feeling_input: str | None

    # Personal System Check output
    calendar_events: list[dict[str, Any]]
    available_windows: list[dict[str, Any]]
    current_time_context: dict[str, Any]
    weather_current: dict[str, Any]

    # Physical domain data
    oura_data: dict[str, Any]
    strava_data: dict[str, Any]
    fatigue_assessment: dict[str, Any]

    # history context (read-only for all domain nodes)
    recent_run_history: list[dict[str, Any]]

    # routing control
    active_domains: list[str]
    skip_reasons: dict[str, str]

    # sub-agent outputs (fan-in target)
    fly_fishing_suggestion: SubAgentSuggestion | None
    physical_suggestion: SubAgentSuggestion | None
    restoration_suggestion: SubAgentSuggestion | None
    growth_suggestion: SubAgentSuggestion | None

    # final output
    final_recommendation: dict[str, Any]
