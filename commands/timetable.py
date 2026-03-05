from data.db import get_conn
from datetime import datetime
import pytz, os

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

def get_today_classes(chat_id):
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).strftime("%A")
    conn = get_conn()
    # Check override first
    today_date = datetime.now(tz).strftime("%Y-%m-%d")
    override = conn.execute(
        "SELECT mapped_day FROM overrides WHERE chat_id=? AND date=?",
        (str(chat_id), today_date)
    ).fetchone()
    lookup_day = override["mapped_day"] if override else today
    rows = conn.execute(
        "SELECT subject, time FROM timetable WHERE chat_id=? AND day=? ORDER BY time",
        (str(chat_id), lookup_day)
    ).fetchall()
    conn.close()
    classes = [{"subject": r["subject"], "time": r["time"]} for r in rows]
    return today, classes

def get_week_classes(chat_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT day, subject, time FROM timetable WHERE chat_id=? ORDER BY day, time",
        (str(chat_id),)
    ).fetchall()
    conn.close()
    return [{"day": r["day"], "subject": r["subject"], "time": r["time"]} for r in rows]

def add_class(chat_id, day, subject, time):
    conn = get_conn()
    conn.execute(
        "INSERT INTO timetable (chat_id, day, subject, time) VALUES (?, ?, ?, ?)",
        (str(chat_id), day.capitalize(), subject, time)
    )
    conn.commit()
    conn.close()

def remove_class(chat_id, day, subject):
    conn = get_conn()
    conn.execute(
        "DELETE FROM timetable WHERE chat_id=? AND day=? AND subject=?",
        (str(chat_id), day.capitalize(), subject)
    )
    conn.commit()
    conn.close()

def set_override(chat_id, date, mapped_day):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO overrides (chat_id, date, mapped_day) VALUES (?, ?, ?)",
        (str(chat_id), date, mapped_day)
    )
    conn.commit()
    conn.close()

def clear_override(chat_id, date):
    conn = get_conn()
    conn.execute(
        "DELETE FROM overrides WHERE chat_id=? AND date=?",
        (str(chat_id), date)
    )
    conn.commit()
    conn.close()
