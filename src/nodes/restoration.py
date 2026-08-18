from hobbymaxxing import config, llm_utils
from state import State, SubAgentSuggestion


def restoration(state: State) -> dict:
    prompt = llm_utils.load_prompt(
        "restoration",
        time_of_day=state.get("current_time_context", {}).get("time_of_day", "unknown"),
        available_windows=state.get("available_windows", []),
        feeling=state.get("user_feeling_input") or "not specified",
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
    return {"restoration_suggestion": suggestion}
