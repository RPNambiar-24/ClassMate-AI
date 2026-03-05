import os
import pytz
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from data.db import get_conn

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _today_str():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%A")


def _today_date():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%Y-%m-%d")


def _resolve_day(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT mapped_day FROM overrides WHERE chat_id=%s AND date=%s",
        (str(chat_id), _today_date())
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else _today_str()


def view_timetable(chat_id, day=None):
    conn = get_conn()
    cur = conn.cursor()
    if day is None or day.lower() == "all":
        cur.execute(
            "SELECT day, time, subject FROM timetable WHERE chat_id=%s ORDER BY day, time",
            (str(chat_id),)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows:
            return "📭 No timetable found. Use `/addclass` or send a JSON file."
        result = "📅 *Full Week Timetable*\n"
        current_day = ""
        for r in rows:
            if r[0] != current_day:
                current_day = r[0]
                result += f"\n*{current_day}*\n"
            result += f"  🕐 {r[1]} — {r[2]}\n"
        return result
    else:
        day = day.capitalize()
        cur.execute(
            "SELECT time, subject FROM timetable WHERE chat_id=%s AND day=%s ORDER BY time",
            (str(chat_id), day)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows:
            return f"📭 No classes found for *{day}*."
        result = f"📅 *{day}'s Classes*\n\n"
        for r in rows:
            result += f"🕐 {r[0]} — {r[1]}\n"
        return result


def get_today_classes(chat_id):
    day = _resolve_day(chat_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT time, subject FROM timetable WHERE chat_id=%s AND day=%s ORDER BY time",
        (str(chat_id), day)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return day, [{"time": r[0], "subject": r[1]} for r in rows]


def add_class(chat_id, day, time, subject):
    day = day.capitalize()
    if day not in DAYS:
        return f"❌ Invalid day: *{day}*. Use Monday–Sunday."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO timetable (chat_id, day, subject, time) VALUES (%s, %s, %s, %s)",
        (str(chat_id), day, subject, time)
    )
    conn.commit()
    cur.close()
    conn.close()
    return f"✅ Added *{subject}* on *{day}* at *{time}*."


def remove_class(chat_id, day, time):
    day = day.capitalize()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM timetable WHERE chat_id=%s AND day=%s AND time=%s",
        (str(chat_id), day, time)
    )
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return f"✅ Removed class on *{day}* at *{time}*." if deleted else f"❌ No class found on *{day}* at *{time}*."


def override_today(chat_id, text):
    if not text.strip():
        return "Usage: `/override HH:MM Subject, HH:MM Subject`"
    today_date = _today_date()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM overrides WHERE chat_id=%s AND date=%s", (str(chat_id), today_date))
    cur.execute(
        "INSERT INTO overrides (chat_id, date, mapped_day) VALUES (%s, %s, %s)",
        (str(chat_id), today_date, "OVERRIDE")
    )
    cur.execute("DELETE FROM timetable WHERE chat_id=%s AND day='OVERRIDE'", (str(chat_id),))
    entries = [e.strip() for e in text.split(",")]
    for entry in entries:
        parts = entry.split(" ", 1)
        if len(parts) == 2:
            cur.execute(
                "INSERT INTO timetable (chat_id, day, time, subject) VALUES (%s, 'OVERRIDE', %s, %s)",
                (str(chat_id), parts[0], parts[1])
            )
    conn.commit()
    cur.close()
    conn.close()
    return f"✅ Today's timetable overridden with {len(entries)} class(es)."


def clear_override(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM overrides WHERE chat_id=%s AND date=%s", (str(chat_id), _today_date()))
    cur.execute("DELETE FROM timetable WHERE chat_id=%s AND day='OVERRIDE'", (str(chat_id),))
    conn.commit()
    cur.close()
    conn.close()
    return "✅ Today's override cleared. Back to normal timetable."


def set_saturday_override(chat_id, arg):
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    days_until_saturday = (5 - now.weekday()) % 7 or 7
    saturday_date = (now + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")
    arg = arg.strip().capitalize()
    if not arg:
        return "Usage: `/saturday Monday` or `/saturday holiday` or `/saturday normal`"
    conn = get_conn()
    cur = conn.cursor()
    if arg.lower() == "holiday":
        cur.execute(
            "INSERT INTO overrides (chat_id, date, mapped_day) VALUES (%s, %s, %s) ON CONFLICT (chat_id, date) DO UPDATE SET mapped_day=%s",
            (str(chat_id), saturday_date, "holiday", "holiday")
        )
        msg = f"✅ Saturday ({saturday_date}) set as *holiday* 🎉"
    elif arg.lower() == "normal":
        cur.execute("DELETE FROM overrides WHERE chat_id=%s AND date=%s", (str(chat_id), saturday_date))
        msg = f"✅ Saturday ({saturday_date}) set to *normal* Saturday timetable."
    elif arg.capitalize() in DAYS:
        mapped = arg.capitalize()
        cur.execute(
            "INSERT INTO overrides (chat_id, date, mapped_day) VALUES (%s, %s, %s) ON CONFLICT (chat_id, date) DO UPDATE SET mapped_day=%s",
            (str(chat_id), saturday_date, mapped, mapped)
        )
        msg = f"✅ Saturday ({saturday_date}) will follow *{mapped}*'s timetable."
    else:
        msg = f"❌ Unknown option: `{arg}`. Use a day name, `holiday`, or `normal`."
    conn.commit()
    cur.close()
    conn.close()
    return msg


def import_timetable(chat_id, data):
    if not isinstance(data, dict):
        return "❌ JSON must be an object with day names as keys."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM timetable WHERE chat_id=%s AND day != 'OVERRIDE'", (str(chat_id),))
    count = 0
    for day, classes in data.items():
        day = day.capitalize()
        if day not in DAYS:
            continue
        for cls in classes:
            if "time" in cls and "subject" in cls:
                cur.execute(
                    "INSERT INTO timetable (chat_id, day, time, subject) VALUES (%s, %s, %s, %s)",
                    (str(chat_id), day, cls["time"], cls["subject"])
                )
                count += 1
    conn.commit()
    cur.close()
    conn.close()
    return f"✅ Imported *{count}* classes successfully!"
