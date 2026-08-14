from hobbymaxxing.state import State, SubAgentSuggestion


def physical(state: State) -> dict:
    suggestion: SubAgentSuggestion = {
        "hobby": "strength_training",
        "confidence": 0.5,
        "reasoning": "stub suggestion, Oura/Strava not yet wired",
        "metadata": {},
    }
    return {"physical_suggestion": suggestion}
