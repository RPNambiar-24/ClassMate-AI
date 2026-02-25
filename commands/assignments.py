import json
from datetime import datetime

ASSIGNMENTS_PATH = "data/assignments.json"


def _load():
    with open(ASSIGNMENTS_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(ASSIGNMENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def add_assignment(subject: str, title: str, due_date: str, type_: str = "assignment") -> str:
    """
    Add assignment/test.
    !add_assignment Physics "Newton's Laws HW" 2026-03-01
    !add_test Maths "Unit Test" 2026-03-05
    """
    data = _load()
    entry = {
        "id": len(data) + 1,
        "type": type_,
        "subject": subject,
        "title": title,
        "due_date": due_date,
        "done": False,
        "added_on": datetime.now().strftime("%Y-%m-%d")
    }
    data.append(entry)
    _save(data)
    emoji = "📝" if type_ == "assignment" else "📋"
    return f"{emoji} Added *{title}* ({subject}) due *{due_date}*."


def view_assignments(filter_type: str = None) -> str:
    data = _load()
    today = datetime.now().strftime("%Y-%m-%d")
    pending = [d for d in data if not d["done"] and d["due_date"] >= today]
    if filter_type:
        pending = [d for d in pending if d["type"] == filter_type]
    if not pending:
        return "🎉 No pending items!"

    pending.sort(key=lambda x: x["due_date"])
    lines = ["📌 *Upcoming Items*\n"]
    for item in pending:
        emoji = "📝" if item["type"] == "assignment" else "📋"
        days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
        urgency = "🔴" if days_left <= 1 else "🟡" if days_left <= 3 else "🟢"
        lines.append(
            f"{urgency} {emoji} [#{item['id']}] *{item['title']}* — {item['subject']}\n"
            f"   📅 Due: {item['due_date']} ({days_left}d left)"
        )
    return "\n".join(lines)


def mark_done(item_id: int) -> str:
    data = _load()
    for item in data:
        if item["id"] == item_id:
            item["done"] = True
            _save(data)
            return f"✅ Marked *{item['title']}* as done!"
    return f"❌ No item with ID #{item_id}."


def get_due_soon(days: int = 1) -> list:
    """Return items due within `days` days (for reminders)."""
    data = _load()
    today = datetime.now().strftime("%Y-%m-%d")
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
