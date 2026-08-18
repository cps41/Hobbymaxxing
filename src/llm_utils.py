import json
import re
from typing import Any

from hobbymaxxing import config


def load_prompt(name: str, **kwargs: Any) -> str:
    """Load prompts/{name}.md and fill in its {placeholder} fields."""
    template = (config.PROMPTS_DIR / f"{name}.md").read_text()
    return template.format(**kwargs)


def parse_json_response(text: str) -> dict[str, Any]:
    """LLMs sometimes wrap JSON in prose or code fences despite instructions;
    pull out the first {...} block rather than assuming a clean response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {text!r}")
    return json.loads(match.group(0))
