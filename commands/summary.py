from datetime import datetime
from commands.timetable import get_today_classes
from commands.assignments import get_due_soon, get_all_pending
from utils.groq_ai import ask_ai
from utils.weather import get_weather
from data.db import get_user_name


def build_daily_summary(chat_id: int) -> str:
    name = get_user_name(chat_id)
    day_name, classes = get_today_classes(chat_id)
    today = datetime.now().strftime("%A, %d %B %Y")

    class_lines = "\n".join(
        f"- {c['time']}: {c['subject']}"
        for c in sorted(classes, key=lambda x: x.get("time", ""))
    ) if classes else "No classes today."

    due_today = get_due_soon(chat_id, 0)
    due_tomorrow = get_due_soon(chat_id, 1)
    due_week = get_due_soon(chat_id, 7)

    due_text = ""
    if due_today:
        due_text += "DUE TODAY: " + ", ".join(i["subject"] for i in due_today) + "\n"
    if due_tomorrow:
        due_text += "DUE TOMORROW: " + ", ".join(i["subject"] for i in due_tomorrow) + "\n"
    if due_week:
        due_text += "DUE THIS WEEK: " + ", ".join(
            f"{i['subject']} ({i['due_date']})" for i in due_week
        )

    weather = get_weather()
    prompt = f"""You are a friendly WhatsApp student assistant for {name}.
Today is {today}.
Classes: {class_lines}
Deadlines: {due_text if due_text else 'Nothing due soon.'}
Write a short Good Morning (max 10 lines). Use *bold* and emojis.
Include: greeting, today's schedule, urgent deadlines, one motivational line."""

    msg = ask_ai(prompt)
    return f"{msg}\n\n{weather}" if weather else msg


def build_escalation_message(item: dict, days_left: int) -> str:
    mapping = {
        7: ("🟢 *Heads Up!*", "gentle reminder"),
        3: ("🟡 *Reminder!*", "study tip for"),
        1: ("🔴 *Urgent!*", "preparation strategy for"),
        0: ("🚨 *Due Today!*", "last-minute tips for"),
    }
    title, context = mapping.get(days_left, ("📌 *Reminder*", "tips for"))
    type_label = "Test" if item["type"] == "test" else "Assignment"
    prompt = f"""Give {context} a {item['subject']} {type_label} due in {days_left} day(s).
2-3 lines max. Use *bold*. Be specific."""
    tip = ask_ai(prompt, max_tokens=150)
    return (
        f"{title}\n"
        f"{'📋' if item['type'] == 'test' else '📝'} *{item['subject']}* {type_label}\n"
        f"📅 Due: {item['due_date']} ({days_left}d left)\n\n{tip}"
    )


def build_weekly_report(chat_id: int) -> str:
    pending = get_all_pending(chat_id)
    pending_text = "\n".join(
        f"- {i['subject']} ({i['due_date']})"
        for i in sorted(pending, key=lambda x: x["due_date"])
    ) if pending else "Nothing pending."

    subject_load = {}
    for item in pending:
        subject_load[item["subject"]] = subject_load.get(item["subject"], 0) + 1

    load_text = "\n".join(f"- {s}: {c} item(s)" for s, c in subject_load.items()) or "All clear!"

    prompt = f"""Student productivity assistant.
Pending: {pending_text}
Workload: {load_text}
Weekly summary (max 12 lines). Use *bold* and emojis.
Include: pending overview, top 3 priorities, motivational close."""
    return ask_ai(prompt, max_tokens=600)
