from datetime import datetime
from commands.timetable import get_today_classes
from commands.assignments import get_due_soon, get_all_pending
from utils.groq_ai import ask_ai
from utils.weather import get_weather


def build_daily_summary() -> str:
    day_name, classes = get_today_classes()
    today = datetime.now().strftime("%A, %d %B %Y")

    class_lines = "\n".join(
        [f"- {c.get('time', c.get('start'))}: {c['subject']}"
         for c in sorted(classes, key=lambda x: x.get("time", x.get("start", "")))]
    ) if classes else "No classes today."

    due_today = get_due_soon(0)
    due_tomorrow = get_due_soon(1)
    due_week = get_due_soon(7)

    due_text = ""
    if due_today:
        due_text += "DUE TODAY: " + ", ".join([f"{i['subject']}" for i in due_today]) + "\n"
    if due_tomorrow:
        due_text += "DUE TOMORROW: " + ", ".join([f"{i['subject']}" for i in due_tomorrow]) + "\n"
    if due_week:
        due_text += "DUE THIS WEEK: " + ", ".join(
            [f"{i['subject']} ({i['due_date']})" for i in due_week]
        )

    weather = get_weather()

    prompt = f"""You are a friendly WhatsApp student assistant bot.
Today is {today}.

Classes:
{class_lines}

Deadlines:
{due_text if due_text else "Nothing due soon."}

Write a short Good Morning message (max 10 lines). Use WhatsApp *bold* and emojis.
Include: greeting, today's schedule, urgent deadlines if any, one motivational line.
Keep it concise and upbeat."""

    ai_summary = ask_ai(prompt)

    # Append weather separately
    if weather:
        return f"{ai_summary}\n\n{weather}"
    return ai_summary


def build_weekly_report() -> str:
    from commands.assignments import get_weekly_stats, get_all_pending
    stats = get_weekly_stats()
    pending = get_all_pending()

    pending_text = "\n".join(
        [f"- {i['subject']} ({i['due_date']})" for i in sorted(pending, key=lambda x: x["due_date"])]
    ) if pending else "Nothing pending."

    subject_load = "\n".join(
        [f"- {s}: {c} item(s)" for s, c in stats["subject_load"].items()]
    ) if stats["subject_load"] else "All clear!"

    prompt = f"""You are a student productivity assistant on WhatsApp.

Weekly Summary:
- Completed this week: {stats['completed_this_week']} tasks
- Still pending: {stats['pending_count']} tasks

Pending items:
{pending_text}

Subject workload:
{subject_load}

Write a Sunday evening weekly report (max 12 lines). Use WhatsApp *bold* and emojis.
Include: what was accomplished, what's coming next week, top 3 priority subjects, motivational close."""

    return ask_ai(prompt, max_tokens=600)


def build_escalation_message(item: dict, days_left: int) -> str:
    urgency_map = {
        7: ("🟢 *Heads Up!*", "gentle reminder"),
        3: ("🟡 *Reminder!*", "study tip for"),
        1: ("🔴 *Urgent!*", "preparation strategy for"),
        0: ("🚨 *Due Today!*", "last-minute tips for")
    }
    emoji_title, context = urgency_map.get(days_left, ("📌 *Reminder*", "tips for"))
    type_label = "Test" if item["type"] == "test" else "Assignment"

    prompt = f"""Give a {context} {item['subject']} {type_label} due in {days_left} day(s).
2-3 lines max. WhatsApp *bold* format. Be specific and actionable."""

    tip = ask_ai(prompt, max_tokens=150)
    return (
        f"{emoji_title}\n"
        f"{'📋' if item['type'] == 'test' else '📝'} *{item['subject']}* {type_label}\n"
        f"📅 Due: {item['due_date']} ({days_left}d left)\n\n"
        f"{tip}"
    )
