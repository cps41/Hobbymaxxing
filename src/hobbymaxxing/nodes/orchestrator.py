from hobbymaxxing.state import State

ALL_DOMAINS = ["fly_fishing", "physical", "restoration", "growth"]


def route_decision(state: State) -> dict:
    """Rule-based node: decide which domain nodes to fan out to, and record
    the decision in state (conditional-edge functions can't write state
    themselves, only node return values are merged).

    Milestone 1 stub rule: skip fly_fishing if it's dark out, per the
    Personal System Check stub context. Real weather/window rules land
    in milestone 6.
    """
    active = list(ALL_DOMAINS)
    skip_reasons: dict[str, str] = {}

    if state.get("current_time_context", {}).get("is_dark"):
        active.remove("fly_fishing")
        skip_reasons["fly_fishing"] = "dark out"

    return {"active_domains": active, "skip_reasons": skip_reasons}


def route(state: State) -> list[str]:
    """Conditional edge: fan out to whatever route_decision already chose."""
    return state["active_domains"]


def synthesize(state: State) -> dict:
    """Fan-in node: combine whichever suggestions were produced into one
    final recommendation. Milestone 1 stub: pick the highest-confidence
    suggestion; milestone 3 replaces this with a real LLM call.
    """
    candidates = [
        state.get("fly_fishing_suggestion"),
        state.get("physical_suggestion"),
        state.get("restoration_suggestion"),
        state.get("growth_suggestion"),
    ]
    candidates = [c for c in candidates if c is not None]

    if not candidates:
        best = {"hobby": "rest", "reasoning": "no suggestions available", "confidence": 0.0, "metadata": {}}
    else:
        best = max(candidates, key=lambda c: c["confidence"])

    return {
        "final_recommendation": {
            "hobby": best["hobby"],
            "reasoning": best["reasoning"],
            "alternatives": [c["hobby"] for c in candidates if c is not best],
        }
    }
