import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = "token.json"
CALENDAR_ID = "primary"


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
            # Update env token (local only)
            if os.path.exists(TOKEN_PATH):
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
        else:
            print("[Calendar] No valid credentials.")
            return None

    return build("calendar", "v3", credentials=creds)



def create_event(subject: str, due_date: str, type_: str = "assignment") -> str:
    """Create a Google Calendar event for an assignment or test."""
    service = _get_service()
    if not service:
        return "⚠️ Google Calendar not connected."

    try:
        type_label = "Test" if type_ == "test" else "Assignment"
        emoji = "📋" if type_ == "test" else "📝"

        # All-day event on due date
        event = {
            "summary": f"{emoji} {type_label}: {subject}",
            "description": f"{type_label} for {subject} — added via WhatsApp Bot",
            "start": {"date": due_date},
            "end":   {"date": due_date},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 24 * 60},   # 1 day before
                    {"method": "popup", "minutes": 8 * 60},    # 8 hours before (morning)
                ]
            }
        }

        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"📅 Added to Google Calendar!\n🔗 {created.get('htmlLink', '')}"

    except Exception as e:
        print(f"[Calendar] Create event error: {e}")
        return "⚠️ Could not add to Google Calendar."


def sync_timetable() -> str:
    """Push full weekly timetable as recurring Google Calendar events."""
    service = _get_service()
    if not service:
        return "⚠️ Google Calendar not connected."

    from commands.timetable import _load_timetable

    timetable = _load_timetable()
    DAYS_MAP = {
        "Monday": "MO", "Tuesday": "TU", "Wednesday": "WE",
        "Thursday": "TH", "Friday": "FR", "Saturday": "SA", "Sunday": "SU"
    }
    # Next Monday as start date anchor
    today = datetime.now()
    days_ahead = (0 - today.weekday()) % 7
    next_monday = today + timedelta(days=days_ahead)

    count = 0
    for day_name, classes in timetable.items():
        if not classes:
            continue
        day_offset = list(DAYS_MAP.keys()).index(day_name)
        class_date = next_monday + timedelta(days=day_offset)

        for cls in classes:
            cls_time = cls.get("time", cls.get("start", "08:00"))
            hour, minute = map(int, cls_time.split(":"))

            start_dt = class_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end_dt = start_dt + timedelta(minutes=50)  # 50 min class duration

            event = {
                "summary": f"📚 {cls['subject']}",
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": os.getenv("TIMEZONE", "Asia/Kolkata")
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": os.getenv("TIMEZONE", "Asia/Kolkata")
                },
                "recurrence": [f"RRULE:FREQ=WEEKLY;BYDAY={DAYS_MAP[day_name]}"],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 10}  # 10 min before
                    ]
                }
            }

            try:
                service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                count += 1
            except Exception as e:
                print(f"[Calendar] Sync error for {cls['subject']}: {e}")

    return f"✅ Synced *{count} classes* to Google Calendar as weekly recurring events!"


def delete_event_by_title(subject: str, due_date: str) -> str:
    """Delete a calendar event when task is marked done."""
    service = _get_service()
    if not service:
        return ""

    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f"{due_date}T00:00:00Z",
            timeMax=f"{due_date}T23:59:59Z",
            q=subject
        ).execute()

        events = events_result.get("items", [])
        for event in events:
            if subject.lower() in event.get("summary", "").lower():
                service.events().delete(calendarId=CALENDAR_ID, eventId=event["id"]).execute()
                return f"🗑️ Removed *{subject}* from Google Calendar."
    except Exception as e:
        print(f"[Calendar] Delete error: {e}")
    return ""
