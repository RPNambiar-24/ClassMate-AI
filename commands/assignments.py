import json
from datetime import datetime
from utils.google_calendar import create_event, delete_event_by_title
ASSIGNMENTS_PATH = "data/assignments.json"


def _load():
    with open(ASSIGNMENTS_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(ASSIGNMENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def add_assignment(subject: str, due_date: str, type_: str = "assignment") -> str:
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return "❌ Invalid date. Use *YYYY-MM-DD* e.g. `2026-03-01`"

    data = _load()
    entry = {
        "id": len(data) + 1,
        "type": type_,
        "subject": subject,
        "due_date": due_date,
        "done": False,
        "added_on": datetime.now().strftime("%Y-%m-%d")
    }
    data.append(entry)
    _save(data)
    calendar_msg = create_event(subject, due_date, type_)
    return (
        f"{emoji} *{type_label} Added!*\n"
        f"📚 Subject: *{subject}*\n"
        f"📅 Due: *{due_date}* ({days_left}d left)\n"
        f"🆔 ID: #{entry['id']}\n"
        f"{calendar_msg}"
    )
    emoji = "📝" if type_ == "assignment" else "📋"
    type_label = "Assignment" if type_ == "assignment" else "Test"
    days_left = (datetime.strptime(due_date, "%Y-%m-%d") - datetime.now()).days
    return (
        f"{emoji} *{type_label} Added!*\n"
        f"📚 Subject: *{subject}*\n"
        f"📅 Due: *{due_date}* ({days_left}d left)\n"
        f"🆔 ID: #{entry['id']}"
    )


def view_assignments(filter_type: str = None) -> str:
    data = _load()
    today = datetime.now().strftime("%Y-%m-%d")
    pending = [d for d in data if not d["done"] and d["due_date"] >= today]

    if filter_type:
        pending = [d for d in pending if d["type"] == filter_type]

    if not pending:
        return "🎉 No pending items!"

    pending.sort(key=lambda x: x["due_date"])

    if filter_type == "assignment":
        header = "📝 *Upcoming Assignments*\n"
    elif filter_type == "test":
        header = "📋 *Upcoming Tests*\n"
    else:
        header = "📌 *All Upcoming Tasks*\n"

    lines = [header]
    for item in pending:
        emoji = "📝" if item["type"] == "assignment" else "📋"
        days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
        urgency = "🔴" if days_left <= 1 else "🟡" if days_left <= 3 else "🟢"
        lines.append(
            f"{urgency} {emoji} [#{item['id']}] *{item['subject']}*\n"
            f"   📅 {item['due_date']} — {days_left}d left"
        )
    return "\n".join(lines)


def mark_done(item_id: int) -> str:
    data = _load()
    for item in data:
        if item["id"] == item_id:
            item["done"] = True
            _save(data)
            delete_event_by_title(item["subject"], item["due_date"])
            emoji = "📝" if item["type"] == "assignment" else "📋"
            return f"✅ {emoji} *{item['subject']}* marked as done!"
    return f"❌ No item with ID #{item_id}. Use *!tasks* to see IDs."


def delete_assignment(item_id: int) -> str:
    data = _load()
    for item in data:
        if item["id"] == item_id:
            data.remove(item)
            _save(data)
            return f"🗑️ Deleted *{item['subject']}* (#{item_id})."
    return f"❌ No item with ID #{item_id}."


def get_due_soon(days: int = 1) -> list:
    data = _load()
    result = []
    for item in data:
        if item["done"]:
            continue
        try:
            due = datetime.strptime(item["due_date"], "%Y-%m-%d")
            diff = (due - datetime.now()).days
            if 0 <= diff <= days:
                result.append(item)
        except Exception:
            pass
    return result


def get_all_pending() -> list:
    data = _load()
    today = datetime.now().strftime("%Y-%m-%d")
    return [d for d in data if not d["done"] and d["due_date"] >= today]


def get_weekly_stats() -> dict:
    data = _load()
    today = datetime.now()
    completed_this_week = [
        d for d in data
        if d["done"] and
        (today - datetime.strptime(d["added_on"], "%Y-%m-%d")).days <= 7
    ]
    subject_counts = {}
    for item in data:
        if not item["done"]:
            subject_counts[item["subject"]] = subject_counts.get(item["subject"], 0) + 1
    return {
        "completed_this_week": len(completed_this_week),
        "pending_count": len([d for d in data if not d["done"]]),
        "subject_load": subject_counts
    }

