import json
import os
from datetime import datetime, timedelta
import pytz
from data.db import get_conn


def get_today_classes(chat_id: int, use_override=True):
    today_name = datetime.now().strftime("%A")
    today_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    classes = [
        dict(r) for r in conn.execute(
            "SELECT time, subject FROM timetable WHERE chat_id=? AND day=? ORDER BY time",
            (chat_id, today_name)
        ).fetchall()
    ]

    if use_override:
        override = conn.execute(
            "SELECT date, classes FROM overrides WHERE chat_id=?", (chat_id,)
        ).fetchone()
        if override and override["date"] == today_date:
            classes = json.loads(override["classes"])

        elif today_name == "Saturday":
            sat = conn.execute(
                "SELECT classes FROM saturday_overrides WHERE chat_id=? AND date=?",
                (chat_id, today_date)
            ).fetchone()
            if sat:
                classes = json.loads(sat["classes"])

    conn.close()
    return today_name, classes


def view_timetable(chat_id: int, day: str = None) -> str:
    conn = get_conn()
    days = [day.capitalize()] if day and day.lower() != "all" else \
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    lines = []
    for d in days:
        rows = conn.execute(
            "SELECT time, subject FROM timetable WHERE chat_id=? AND day=? ORDER BY time",
            (chat_id, d)
        ).fetchall()
        if rows:
            lines.append(f"\n*{d}*")
            for r in rows:
                lines.append(f"  🕐 {r['time']} — {r['subject']}")

    conn.close()
    if not lines:
        return "📅 No timetable found. Use /addclass to add classes."
    header = f"📅 *{day.capitalize()} Timetable*" if day and day.lower() != "all" else "📅 *Full Weekly Timetable*"
    return header + "\n" + "\n".join(lines)


def add_class(chat_id: int, day: str, time: str, subject: str) -> str:
    day = day.capitalize()
    valid_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    if day not in valid_days:
        return f"❌ Invalid day: {day}"
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM timetable WHERE chat_id=? AND day=? AND time=?",
        (chat_id, day, time)
    ).fetchone()
    if existing:
        conn.close()
        return f"⚠️ Conflict: already a class at *{time}* on *{day}*."
    conn.execute(
        "INSERT INTO timetable (chat_id, day, time, subject) VALUES (?,?,?,?)",
        (chat_id, day, time, subject)
    )
    conn.commit()
    conn.close()
    return f"✅ Added *{subject}* at *{time}* on *{day}*."


def remove_class(chat_id: int, day: str, time: str) -> str:
    day = day.capitalize()
    conn = get_conn()
    result = conn.execute(
        "DELETE FROM timetable WHERE chat_id=? AND day=? AND time=?",
        (chat_id, day, time)
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        return f"❌ No class at {time} on {day}."
    return f"✅ Removed class at *{time}* on *{day}*."


def override_today(chat_id: int, classes_str: str) -> str:
    today_date = datetime.now().strftime("%Y-%m-%d")
    classes = []
    for entry in classes_str.split(","):
        parts = entry.strip().split(" ", 1)
        if len(parts) == 2:
            classes.append({"time": parts[0].strip(), "subject": parts[1].strip()})
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO overrides (chat_id, date, classes) VALUES (?,?,?)",
        (chat_id, today_date, json.dumps(classes))
    )
    conn.commit()
    conn.close()
    lines = ["✅ *Today's timetable overridden:*"]
    for c in classes:
        lines.append(f"  🕐 {c['time']} — {c['subject']}")
    return "\n".join(lines)


def clear_override(chat_id: int) -> str:
    conn = get_conn()
    conn.execute("DELETE FROM overrides WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()
    return "✅ Today's override cleared."


def set_saturday_override(chat_id: int, input_day: str) -> str:
    tz = pytz.timezone(os.getenv("TIMEZONE", "Asia/Kolkata"))
    now = datetime.now(tz)
    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday_date = (now + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")

    input_day = input_day.strip().capitalize()
    conn = get_conn()

    if input_day == "Holiday":
        conn.execute(
            "INSERT OR REPLACE INTO saturday_overrides (chat_id, date, day_used, classes) VALUES (?,?,?,?)",
            (chat_id, saturday_date, "holiday", json.dumps([]))
        )
        conn.commit()
        conn.close()
        return f"✅ Saturday ({saturday_date}) set as *Holiday* 🎉"

    if input_day == "Normal":
        conn.execute(
            "DELETE FROM saturday_overrides WHERE chat_id=? AND date=?",
            (chat_id, saturday_date)
        )
        conn.commit()
        conn.close()
        return f"✅ Saturday ({saturday_date}) uses normal Saturday timetable."

    rows = conn.execute(
        "SELECT time, subject FROM timetable WHERE chat_id=? AND day=? ORDER BY time",
        (chat_id, input_day)
    ).fetchall()

    if not rows:
        conn.close()
        return f"❌ No timetable found for *{input_day}*."

    classes = [{"time": r["time"], "subject": r["subject"]} for r in rows]
    conn.execute(
        "INSERT OR REPLACE INTO saturday_overrides (chat_id, date, day_used, classes) VALUES (?,?,?,?)",
        (chat_id, saturday_date, input_day, json.dumps(classes))
    )
    conn.commit()
    conn.close()

    lines = [f"✅ Saturday ({saturday_date}) follows *{input_day}'s* timetable:"]
    for c in classes:
        lines.append(f"  🕐 {c['time']} — {c['subject']}")
    return "\n".join(lines)


def import_timetable(chat_id: int, timetable_json: dict) -> str:
    """Import full timetable from JSON dict."""
    conn = get_conn()
    conn.execute("DELETE FROM timetable WHERE chat_id=?", (chat_id,))
    count = 0
    for day, classes in timetable_json.items():
        for cls in classes:
            time_val = cls.get("time", cls.get("start", ""))
            subject = cls.get("subject", "")
            if time_val and subject:
                conn.execute(
                    "INSERT INTO timetable (chat_id, day, time, subject) VALUES (?,?,?,?)",
                    (chat_id, day, time_val, subject)
                )
                count += 1
    conn.commit()
    conn.close()
    return f"✅ Imported *{count} classes* into your timetable!"
