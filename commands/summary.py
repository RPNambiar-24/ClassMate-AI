import os
from datetime import datetime
from commands.timetable import get_today_classes, view_timetable
from commands.assignments import get_all_pending

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

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
            urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
            lines.append(f"{urg} {emoji} *{p['subject']}* — {p['due_date']} ({days_left}d left)")
    else:
        lines.append("All clear! ✅")

    return "\n".join(lines)

def build_weekly_report(chat_id):
    from commands.timetable import view_timetable
    timetable = view_timetable(chat_id, "all")
    pending = get_all_pending(chat_id)

    lines = ["📊 *Weekly Overview*\n", timetable, "\n📌 *All Pending Tasks*\n"]
    if pending:
        for p in pending:
            emoji = "📝" if p["type"] == "assignment" else "📋"
            days_left = (datetime.strptime(p["due_date"], "%Y-%m-%d") - datetime.now()).days
            urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
            lines.append(f"{urg} {emoji} *{p['subject']}* ({p['type']}) — {p['due_date']} ({days_left}d left)")
    else:
        lines.append("No pending tasks! ✅")

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
