import os
import requests
from datetime import datetime
from groq import Groq
from commands.timetable import get_today_classes, view_timetable
from commands.assignments import get_all_pending

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
CITY = os.getenv("CITY", "Chennai")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_weather():
    if not WEATHER_API_KEY:
        return None
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5).json()
        temp = round(r["main"]["temp"])
        feels = round(r["main"]["feels_like"])
        desc = r["weather"][0]["description"].capitalize()
        humidity = r["main"]["humidity"]
        return f"{desc}, {temp}°C (feels like {feels}°C), Humidity: {humidity}%"
    except Exception as e:
        print(f"[Weather Error] {e}")
        return None


def build_daily_summary(chat_id):
    today, classes = get_today_classes(chat_id)
    pending = get_all_pending(chat_id)
    weather = get_weather()

    # --- Structured blocks ---
    weather_block = ""
    if weather:
        weather_block = f"🌤️ *Weather in {CITY}*\n{weather}\n\n"

    schedule_block = f"📅 *{today}'s Classes*\n"
    if classes:
        for c in classes:
            schedule_block += f"  🕐 {c['time']} — {c['subject']}\n"
    else:
        schedule_block += "  No classes today! 🎉\n"

    tasks_block = "\n📌 *Pending Tasks*\n"
    if pending:
        for p in pending:
            emoji = "📝" if p["type"] == "assignment" else "📋"
            days_left = (datetime.strptime(p["due_date"], "%Y-%m-%d") - datetime.now()).days
            urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
            tasks_block += f"  {urg} {emoji} *{p['subject']}* — {p['due_date']} ({days_left}d left)\n"
    else:
        tasks_block += "  All clear! ✅\n"

    # --- AI motivation ---
    class_lines = "\n".join([f"- {c['time']}: {c['subject']}" for c in classes]) or "No classes"
    task_lines = "\n".join([f"- {p['subject']} ({p['type']}) due {p['due_date']}" for p in pending]) or "None"
    weather_line = f"Weather: {weather}" if weather else "Weather: unavailable"

    prompt = f"""You are ClassMate AI, a warm and friendly academic assistant.
Today is {today}. Write a natural, friendly morning greeting (3-5 lines) for a student.
Mention the weather briefly if it's notable. Reference how busy or light the day looks.
If tasks are due soon, gently remind them. End with a short motivational line.
Do NOT repeat the full schedule or task list — just reference them naturally.
Use emojis naturally. Be conversational, not robotic.

{weather_line}
Classes today: {class_lines}
Pending tasks: {task_lines}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180
        )
        ai_text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq Error] {e}")
        ai_text = "💪 Stay focused and give it your best today!"

    return (
        f"{weather_block}"
        f"{schedule_block}"
        f"{tasks_block}\n"
        f"🤖 *ClassMate Says*\n{ai_text}"
    )


def build_weekly_report(chat_id):
    pending = get_all_pending(chat_id)
    _, all_classes = get_today_classes(chat_id)  # for context
    timetable_text = view_timetable(chat_id, "all")

    # --- Pending tasks block ---
    tasks_block = "📌 *Pending Tasks*\n"
    if pending:
        for p in pending:
            emoji = "📝" if p["type"] == "assignment" else "📋"
            days_left = (datetime.strptime(p["due_date"], "%Y-%m-%d") - datetime.now()).days
            urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
            tasks_block += f"  {urg} {emoji} *{p['subject']}* ({p['type']}) — {p['due_date']} ({days_left}d left)\n"
    else:
        tasks_block += "  Nothing pending — great job! ✅\n"

    # --- AI weekly insight ---
    task_lines = "\n".join([
        f"- {p['subject']} ({p['type']}) due {p['due_date']}"
        for p in pending
    ]) or "No pending tasks"

    prompt = f"""You are ClassMate AI, a friendly academic assistant.
Write a natural, encouraging weekly academic overview for a student (5-7 lines).
Mention the workload for the week, highlight urgent tasks if any, and suggest priorities.
End with a motivational closing line.
Do NOT list every class. Be conversational and warm. Use emojis naturally.

Timetable summary:
{timetable_text}

Pending tasks:
{task_lines}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250
        )
        ai_insight = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq Error] {e}")
        ai_insight = "Keep pushing through the week — you're doing great! 💪"

    return (
        f"📊 *Weekly Overview*\n\n"
        f"{timetable_text}\n\n"
        f"{tasks_block}\n"
        f"🤖 *ClassMate Says*\n{ai_insight}"
    )


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
        f"{emoji} *{p['subject']}* ({item['type']})\n"
        f"📅 Due: {item['due_date']}"
    )
