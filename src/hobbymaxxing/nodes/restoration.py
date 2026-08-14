from hobbymaxxing.state import State, SubAgentSuggestion


def restoration(state: State) -> dict:
    suggestion: SubAgentSuggestion = {
        "hobby": "reading",
        "confidence": 0.5,
        "reasoning": "stub suggestion, history-based reasoning not yet wired",
        "metadata": {},
    }
    return {"restoration_suggestion": suggestion}
