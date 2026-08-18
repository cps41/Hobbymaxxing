from hobbymaxxing import config, llm_utils
from state import State

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
    """Fan-in node: one LLM call ranks/combines whichever suggestions were
    produced (None for skipped domains) into a final recommendation."""
    candidates = {
        domain: state.get(f"{domain}_suggestion")
        for domain in ALL_DOMAINS
        if state.get(f"{domain}_suggestion") is not None
    }

    if not candidates:
        return {
            "final_recommendation": {
                "hobby": "rest",
                "reasoning": "no suggestions available",
                "alternatives": [],
            }
        }

    suggestions_text = "\n".join(
        f"- {domain}: hobby={s['hobby']}, confidence={s['confidence']}, reasoning={s['reasoning']!r}"
        for domain, s in candidates.items()
    )

    prompt = llm_utils.load_prompt(
        "synthesize",
        skip_reasons=state.get("skip_reasons", {}),
        suggestions=suggestions_text,
    )

    response = config.get_llm(temperature=0.2).invoke(prompt)
    parsed = llm_utils.parse_json_response(response.content)

    return {
        "final_recommendation": {
            "hobby": parsed["hobby"],
            "reasoning": parsed["reasoning"],
            "alternatives": parsed.get("alternatives", []),
        }
    }
