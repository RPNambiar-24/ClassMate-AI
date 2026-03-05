import os
from datetime import datetime
from groq import Groq
from commands.timetable import get_today_classes, view_timetable
from commands.assignments import get_all_pending

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def build_daily_summary(chat_id):
    today, classes = get_today_classes(chat_id)
    pending = get_all_pending(chat_id)

    # Build raw data string for AI
    class_lines = "\n".join([f"- {c['time']}: {c['subject']}" for c in classes]) or "No classes today"
    task_lines = "\n".join([
        f"- {p['subject']} ({p['type']}) due {p['due_date']}"
        for p in pending
    ]) or "No pending tasks"

    prompt = f"""You are ClassMate AI, a friendly academic assistant.
Today is {today}. Generate a motivating, concise morning summary for a student.

Today's Classes:
{class_lines}

Pending Tasks:
{task_lines}

Keep it friendly, under 150 words. Use emojis. Give a short motivational line at the end."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        ai_text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq Error] {e}")
        # Fallback to plain summary if Groq fails
        ai_text = f"📅 *{today}'s Schedule*\n\n"
        ai_text += "\n".join([f"🕐 {c['time']} — {c['subject']}" for c in classes]) or "No classes 🎉"
        ai_text += "\n\n📌 *Pending Tasks*\n"
        ai_text += "\n".join([f"📝 {p['subject']} — {p['due_date']}" for p in pending]) or "All clear! ✅"


    return ai_text


def build_weekly_report(chat_id):
    timetable = view_timetable(chat_id, "all")
    pending = get_all_pending(chat_id)

    task_lines = "\n".join([
        f"- {p['subject']} ({p['type']}) due {p['due_date']}"
        for p in pending
    ]) or "No pending tasks"

    prompt = f"""You are ClassMate AI. Generate a weekly academic report for a student.

Timetable:
{timetable}

Pending Tasks:
{task_lines}

Give a structured weekly overview with priorities and a motivational closing. Under 200 words. Use emojis."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"📊 *Weekly Report*\n\n{timetable}\n\n📌 Pending:\n{task_lines}"


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


