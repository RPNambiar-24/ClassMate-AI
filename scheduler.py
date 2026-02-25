import os
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv

load_dotenv()

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")


def send_class_reminders():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.timetable import get_today_classes

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    reminder_time = (now + timedelta(minutes=10)).strftime("%H:%M")

    _, classes = get_today_classes()
    chat_id = get_my_chat_id()

    for cls in classes:
        cls_time = cls.get("time", cls.get("start", ""))
        if cls_time == reminder_time:
            msg = (
                f"⏰ *Class Reminder!*\n"
                f"📚 *{cls['subject']}* starts in 10 minutes at *{cls_time}*.\n"
                f"Get ready! 🎒"
            )
            send_message(chat_id, msg)


def send_daily_summary():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.summary import build_daily_summary

    chat_id = get_my_chat_id()
    summary = build_daily_summary()
    send_message(chat_id, f"🌅 *Good Morning, Rishab!*\n\n{summary}")


def send_assignment_reminders():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.assignments import get_due_soon

    due_items = get_due_soon(days=2)
    if not due_items:
        return

    chat_id = get_my_chat_id()
    lines = ["📌 *Deadline Reminder!*\n"]
    for item in due_items:
        emoji = "📝" if item["type"] == "assignment" else "📋"
        due = datetime.strptime(item["due_date"], "%Y-%m-%d")
        days_left = (due - datetime.now()).days
        urgency = "🔴" if days_left <= 0 else "🟡" if days_left == 1 else "🟢"
        lines.append(
            f"{urgency} {emoji} *{item['title']}* — {item['subject']} (due {item['due_date']})"
        )
    send_message(chat_id, "\n".join(lines))


def reset_daily_overrides():
    with open("data/overrides.json", "w") as f:
        json.dump({"date": "", "classes": []}, f)
    print("[Scheduler] Daily overrides reset.")


def start_scheduler():
    tz = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    # Check every minute for 10-min class reminders
    scheduler.add_job(send_class_reminders, "interval", minutes=1, id="class_reminders")

    # Daily summary at 8:00 AM
    scheduler.add_job(
        send_daily_summary,
        CronTrigger(hour=8, minute=0, timezone=tz),
        id="daily_summary"
    )

    # Assignment reminder at 8:00 PM
    scheduler.add_job(
        send_assignment_reminders,
        CronTrigger(hour=20, minute=0, timezone=tz),
        id="assignment_reminder"
    )

    # Reset overrides at midnight
    scheduler.add_job(
        reset_daily_overrides,
        CronTrigger(hour=0, minute=0, timezone=tz),
        id="reset_overrides"
    )

    scheduler.start()
    print("[Scheduler] Started. Jobs: class reminders, daily summary, assignment reminders, override reset.")
