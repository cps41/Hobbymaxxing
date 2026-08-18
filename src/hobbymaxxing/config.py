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

STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
