from hobbymaxxing.state import State, SubAgentSuggestion


def fly_fishing(state: State) -> dict:
    suggestion: SubAgentSuggestion = {
        "hobby": "fly_fishing",
        "confidence": 0.5,
        "reasoning": "stub suggestion, weather/report/traffic not yet wired",
        "metadata": {},
    }
    return {"fly_fishing_suggestion": suggestion}
