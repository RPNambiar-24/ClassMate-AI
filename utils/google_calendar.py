import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = "primary"
TOKEN_PATH = "token.json"


def _get_service():
    creds = None
    token_env = os.getenv("GOOGLE_TOKEN_JSON")

    if token_env:
        creds = Credentials.from_authorized_user_info(json.loads(token_env), SCOPES)
    elif os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if os.path.exists(TOKEN_PATH):
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
        else:
            print("[Calendar] No valid credentials. Run auth_calendar.py locally first.")
            return None

    return build("calendar", "v3", credentials=creds)


def create_event(subject: str, due_date: str, type_: str = "assignment") -> str:
    service = _get_service()
    if not service:
        return "⚠️ Google Calendar not connected."
    try:
        type_label = "Test" if type_ == "test" else "Assignment"
        emoji = "📋" if type_ == "test" else "📝"
        event = {
            "summary": f"{emoji} {type_label}: {subject}",
            "description": f"{type_label} for {subject} — added via WhatsApp Bot",
            "start": {"date": due_date},
            "end": {"date": due_date},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 8 * 60},
                ],
            },
        }
        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        link = created.get("htmlLink", "")
        return f"📅 Added to Google Calendar.\n🔗 {link}" if link else "📅 Added to Google Calendar."
    except Exception as e:
        print(f"[Calendar] Create error: {e}")
        return "⚠️ Could not add to Google Calendar."


def delete_event_by_title(subject: str, due_date: str) -> str:
    service = _get_service()
    if not service:
        return ""
    try:
        result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f"{due_date}T00:00:00Z",
            timeMax=f"{due_date}T23:59:59Z",
            q=subject,
        ).execute()
        for event in result.get("items", []):
            if subject.lower() in event.get("summary", "").lower():
                service.events().delete(calendarId=CALENDAR_ID, eventId=event["id"]).execute()
                return f"🗑️ Removed *{subject}* from Google Calendar."
    except Exception as e:
        print(f"[Calendar] Delete error: {e}")
    return ""
