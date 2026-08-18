from state import State, SubAgentSuggestion


def growth(state: State) -> dict:
    suggestion: SubAgentSuggestion = {
        "hobby": "coding",
        "confidence": 0.5,
        "reasoning": "stub suggestion, history-based reasoning not yet wired",
        "metadata": {},
    }
    return {"growth_suggestion": suggestion}
