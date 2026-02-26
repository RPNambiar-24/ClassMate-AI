import json
import os
from datetime import datetime

TIMETABLE_PATH = "data/timetable.json"
OVERRIDES_PATH = "data/overrides.json"


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


def get_today_classes(use_override=True):
    today_name = datetime.now().strftime("%A")
    today_date = datetime.now().strftime("%Y-%m-%d")
    timetable = _load_timetable()
    classes = timetable.get(today_name, [])

    if use_override:
        overrides = _load_overrides()
        if overrides.get("date") == today_date:
            classes = overrides.get("classes", classes)

    return today_name, classes


def check_conflicts(day: str, new_time: str, classes: list) -> str:
    for cls in classes:
        cls_time = cls.get("time", cls.get("start", ""))
        if cls_time == new_time:
            return f"⚠️ *Conflict!* Already have *{cls['subject']}* at *{new_time}* on *{day}*."
    return ""


def view_timetable(day: str = None) -> str:
    timetable = _load_timetable()
    if day:
        day = day.capitalize()
        if day not in timetable:
            return f"❌ Invalid day: {day}. Use Monday–Sunday."
        classes = timetable[day]
        if not classes:
            return f"📅 {day}: No classes."
        lines = [f"📅 *{day} Timetable*"]
        for c in sorted(classes, key=lambda x: x.get("time", x.get("start", ""))):
            lines.append(f"  🕐 {c.get('time', c.get('start'))} — {c['subject']}")
        return "\n".join(lines)
    else:
        lines = ["📅 *Full Weekly Timetable*"]
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            day_classes = timetable.get(d, [])
            if day_classes:
                lines.append(f"\n*{d}*")
                for c in sorted(day_classes, key=lambda x: x.get("time", x.get("start", ""))):
                    lines.append(f"  🕐 {c.get('time', c.get('start'))} — {c['subject']}")
        return "\n".join(lines)


def add_class(day: str, time: str, subject: str) -> str:
    timetable = _load_timetable()
    day = day.capitalize()
    if day not in timetable:
        return f"❌ Invalid day: {day}"
    conflict = check_conflicts(day, time, timetable[day])
    if conflict:
        return conflict
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
        return f"❌ No class found at {time} on {day}."
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
    return "✅ Today's override cleared. Using normal timetable."
