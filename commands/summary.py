from datetime import datetime
from commands.timetable import get_today_classes
from commands.assignments import get_due_soon
from utils.gemini import ask_gemini


def build_daily_summary() -> str:
    day_name, classes = get_today_classes()
    today = datetime.now().strftime("%A, %d %B %Y")

    # Build class list text
    if classes:
        class_lines = "\n".join(
            [f"- {c['time']}: {c['subject']}" for c in sorted(classes, key=lambda x: x["time"])]
        )
    else:
        class_lines = "No classes today."

    # Due soon items
    due_today = get_due_soon(0)
    due_tomorrow = get_due_soon(1)
    due_this_week = get_due_soon(7)

    due_text = ""
    if due_today:
        due_text += "DUE TODAY: " + ", ".join([f"{i['title']} ({i['subject']})" for i in due_today]) + "\n"
    if due_tomorrow:
        due_text += "DUE TOMORROW: " + ", ".join([f"{i['title']} ({i['subject']})" for i in due_tomorrow]) + "\n"
    if due_this_week:
        due_text += "DUE THIS WEEK: " + ", ".join(
            [f"{i['title']} ({i['subject']}, {i['due_date']})" for i in due_this_week]
        )

    prompt = f"""You are a friendly student assistant bot on WhatsApp.
Today is {today}.

Classes scheduled:
{class_lines}

Deadlines:
{due_text if due_text else "Nothing due soon."}

Write a short, friendly, motivating Good Morning summary (max 10 lines).
Use WhatsApp formatting (*bold*, emojis). Include:
- Greeting with the day
- Today's class schedule
- Urgent deadlines (if any)
- A short motivational line
Keep it concise and upbeat."""

    return ask_gemini(prompt)
