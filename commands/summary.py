from commands.timetable import get_today_classes
from commands.assignments import get_all_pending
from datetime import datetime

def build_daily_summary(chat_id):
    today, classes = get_today_classes(chat_id)
    pending = get_all_pending(chat_id)

    lines = [f"📅 *{today}'s Schedule*\n"]
    if classes:
        for c in classes:
            lines.append(f"🕐 {c['time']} — {c['subject']}")
    else:
        lines.append("No classes today! 🎉")

    lines.append("\n📌 *Pending Tasks*")
    if pending:
        for p in pending:
            emoji = "📝" if p["type"] == "assignment" else "📋"
            days_left = (datetime.strptime(p["due_date"], "%Y-%m-%d") - datetime.now()).days
            lines.append(f"{emoji} {p['subject']} — due {p['due_date']} ({days_left}d left)")
    else:
        lines.append("All clear! ✅")

    return "\n".join(lines)

def build_escalation_message(item, days_left):
    emoji = "📝" if item["type"] == "assignment" else "📋"
    if days_left == 0:
        urgency = "🔴 *DUE TODAY!*"
    elif days_left == 1:
        urgency = "🟠 *Due Tomorrow!*"
    elif days_left == 3:
        urgency = "🟡 Due in 3 days"
    else:
        urgency = "🟢 Due in 7 days"
    return (
        f"{urgency}\n"
        f"{emoji} *{item['subject']}* ({item['type']})\n"
        f"📅 Due: {item['due_date']}"
    )
