import json
import os
from datetime import datetime, timedelta
import pytz

TIMETABLE_PATH = "data/timetable.json"
OVERRIDES_PATH = "data/overrides.json"
SATURDAY_OVERRIDES_PATH = "data/saturday_overrides.json"


def _load_timetable():
    with open(TIMETABLE_PATH, "r") as f:
        return json.load(f)


def _save_timetable(data):
    with open(TIMETABLE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _load_overrides():
    with open(OVERRIDES_PATH, "r") as f:
        return json.load(f)


def _save_overrides(data):
    with open(OVERRIDES_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _load_saturday_overrides():
    try:
        with open(SATURDAY_OVERRIDES_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_saturday_overrides(data):
    with open(SATURDAY_OVERRIDES_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_today_classes(use_override=True):
    today_name = datetime.now().strftime("%A")
    today_date = datetime.now().strftime("%Y-%m-%d")
    timetable = _load_timetable()
    classes = timetable.get(today_name, [])

    if use_override:
        # Check regular daily override first (highest priority)
        overrides = _load_overrides()
        if overrides.get("date") == today_date:
            classes = overrides.get("classes", classes)

        # Check Saturday-specific override
        elif today_name == "Saturday":
            sat_data = _load_saturday_overrides()
            if today_date in sat_data:
                classes = sat_data[today_date]["classes"]

    return today_name, classes


def view_timetable(day: str = None) -> str:
    timetable = _load_timetable()
    if day:
        day = day.capitalize()
        if day not in timetable:
            return f"❌ Invalid day: {day}."
        classes = timetable[day]
        if not classes:
            return f"📅 {day}: No classes."
        lines = [f"📅 *{day} Timetable*"]
        for c in sorted(classes, key=lambda x: x.get("time", x.get("start", ""))):
            t = c.get("time", c.get("start"))
            lines.append(f"  🕐 {t} — {c['subject']}")
        return "\n".join(lines)

    lines = ["📅 *Full Weekly Timetable*"]
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        day_classes = timetable.get(d, [])
        if day_classes:
            lines.append(f"\n*{d}*")
            for c in sorted(day_classes, key=lambda x: x.get("time", x.get("start", ""))):
                t = c.get("time", c.get("start"))
                lines.append(f"  🕐 {t} — {c['subject']}")
    return "\n".join(lines)


def add_class(day: str, time: str, subject: str) -> str:
    timetable = _load_timetable()
    day = day.capitalize()
    if day not in timetable:
        return f"❌ Invalid day: {day}"
    for cls in timetable[day]:
        if cls.get("time", cls.get("start")) == time:
            return f"⚠️ Conflict: already *{cls['subject']}* at *{time}* on *{day}*."
    timetable[day].append({"time": time, "subject": subject})
    _save_timetable(timetable)
    return f"✅ Added *{subject}* at *{time}* on *{day}*."


def remove_class(day: str, time: str) -> str:
    timetable = _load_timetable()
    day = day.capitalize()
    if day not in timetable:
        return f"❌ Invalid day: {day}"
    before = len(timetable[day])
    timetable[day] = [c for c in timetable[day] if c.get("time", c.get("start")) != time]
    if len(timetable[day]) == before:
        return f"❌ No class at {time} on {day}."
    _save_timetable(timetable)
    return f"✅ Removed class at *{time}* on *{day}*."


def override_today(classes_str: str) -> str:
    today_date = datetime.now().strftime("%Y-%m-%d")
    classes = []
    for entry in classes_str.split(","):
        parts = entry.strip().split(" ", 1)
        if len(parts) == 2:
            classes.append({"time": parts[0].strip(), "subject": parts[1].strip()})
    _save_overrides({"date": today_date, "classes": classes})
    lines = ["✅ *Today's timetable overridden:*"]
    for c in classes:
        lines.append(f"  🕐 {c['time']} — {c['subject']}")
    return "\n".join(lines)


def clear_override() -> str:
    _save_overrides({"date": "", "classes": []})
    return "✅ Today's override cleared."


def set_saturday_override(input_day: str) -> str:
    tz = pytz.timezone(os.getenv("TIMEZONE", "Asia/Kolkata"))
    now = datetime.now(tz)

    # Find the coming Saturday
    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday_date = (now + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")

    input_day = input_day.strip().capitalize()

    if input_day == "Holiday":
        sat_data = _load_saturday_overrides()
        sat_data[saturday_date] = {"day_used": "holiday", "classes": []}
        _save_saturday_overrides(sat_data)
        return f"✅ Saturday ({saturday_date}) set as *Holiday* — no classes. 🎉"

    if input_day == "Normal":
        sat_data = _load_saturday_overrides()
        if saturday_date in sat_data:
            del sat_data[saturday_date]
            _save_saturday_overrides(sat_data)
        return f"✅ Saturday ({saturday_date}) will use the *normal Saturday* timetable."

    timetable = _load_timetable()
    if input_day not in timetable:
        return (
            f"❌ Invalid: *{input_day}*\n"
            f"Use a day name (Monday–Sunday), *holiday*, or *normal*."
        )

    classes = timetable[input_day]
    sat_data = _load_saturday_overrides()
    sat_data[saturday_date] = {"day_used": input_day, "classes": classes}
    _save_saturday_overrides(sat_data)

    lines = [f"✅ Saturday ({saturday_date}) will follow *{input_day}'s* timetable:"]
    for c in sorted(classes, key=lambda x: x.get("time", x.get("start", ""))):
        t = c.get("time", c.get("start"))
        lines.append(f"  🕐 {t} — {c['subject']}")
    return "\n".join(lines)
