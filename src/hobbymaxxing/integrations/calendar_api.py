import datetime as dt
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from hobbymaxxing import config

_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_credentials() -> Credentials:
    token_path = Path(config.GOOGLE_CALENDAR_TOKEN_PATH)
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GOOGLE_CALENDAR_CREDENTIALS_PATH, _SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return creds


def get_events(horizon: str = "today") -> list[dict[str, Any]]:
    """Fetch calendar events for today or the next 7 days."""
    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = dt.datetime.now(dt.timezone.utc)
    end = now + dt.timedelta(days=1 if horizon == "today" else 7)

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = []
    for event in events_result.get("items", []):
        start = event["start"].get("dateTime", event["start"].get("date"))
        end_time = event["end"].get("dateTime", event["end"].get("date"))
        events.append({"summary": event.get("summary", "(no title)"), "start": start, "end": end_time})

    return events
