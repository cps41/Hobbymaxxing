import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

HOME_LAT = os.environ.get("HOME_LAT")
HOME_LON = os.environ.get("HOME_LON")

GOOGLE_CALENDAR_CREDENTIALS_PATH = os.environ.get(
    "GOOGLE_CALENDAR_CREDENTIALS_PATH", "data/credentials.json"
)
GOOGLE_CALENDAR_TOKEN_PATH = os.environ.get("GOOGLE_CALENDAR_TOKEN_PATH", "data/token.json")

OURA_PERSONAL_ACCESS_TOKEN = os.environ.get("OURA_PERSONAL_ACCESS_TOKEN")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

LLM_MODEL = os.environ.get("HOBBYMAXXING_LLM_MODEL", "claude-sonnet-4-5-20250929")


def get_llm(*, temperature: float = 0.4):
    """Single place to construct the LangChain chat model, so every node
    shares the same model/config and it's easy to swap providers later."""
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=LLM_MODEL, temperature=temperature, api_key=ANTHROPIC_API_KEY)
