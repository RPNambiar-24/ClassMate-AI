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
    from commands.assignments import get_all_pending

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    reminder_time = (now + timedelta(minutes=10)).strftime("%H:%M")

    _, classes = get_today_classes()
    chat_id = get_my_chat_id()

    for cls in classes:
        cls_time = cls.get("time", cls.get("start", ""))
        if cls_time == reminder_time:
            # Check if any pending assignment for this subject
            pending = get_all_pending()
            subject_tasks = [p for p in pending if p["subject"].lower() == cls["subject"].lower()]

            msg = (
                f"⏰ *Class Reminder!*\n"
                f"📚 *{cls['subject']}* in 10 minutes at *{cls_time}*\n"
                f"Get ready! 🎒"
            )
            if subject_tasks:
                task = subject_tasks[0]
                days_left = (datetime.strptime(task["due_date"], "%Y-%m-%d") - datetime.now()).days
                msg += f"\n\n⚠️ You have a pending {'test' if task['type'] == 'test' else 'assignment'} for this subject due in *{days_left}d*!"

            send_message(chat_id, msg)


def send_daily_summary():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.summary import build_daily_summary

    chat_id = get_my_chat_id()
    summary = build_daily_summary()
    send_message(chat_id, f"🌅 *Good Morning, Rishab!*\n\n{summary}")


def send_escalation_reminders():
    """Smart deadline escalation — fires at 8 AM checking 7, 3, 1, 0 day thresholds."""
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.assignments import get_all_pending
    from commands.summary import build_escalation_message

    chat_id = get_my_chat_id()
    pending = get_all_pending()
    escalation_days = [0, 1, 3, 7]

    for item in pending:
        try:
            due = datetime.strptime(item["due_date"], "%Y-%m-%d")
            days_left = (due - datetime.now()).days
            if days_left in escalation_days:
                msg = build_escalation_message(item, days_left)
                send_message(chat_id, msg)
        except Exception as e:
            print(f"[Scheduler] Escalation error: {e}")


def send_evening_reminder():
    """8 PM — summary of tasks due in 2 days."""
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.assignments import get_due_soon

    due_items = get_due_soon(days=2)
    if not due_items:
        return

    chat_id = get_my_chat_id()
    lines = ["📌 *Evening Deadline Check*\n"]
    for item in due_items:
        emoji = "📝" if item["type"] == "assignment" else "📋"
        due = datetime.strptime(item["due_date"], "%Y-%m-%d")
        days_left = (due - datetime.now()).days
        urgency = "🔴" if days_left <= 0 else "🟡" if days_left == 1 else "🟢"
        lines.append(f"{urgency} {emoji} *{item['subject']}* — due {item['due_date']} ({days_left}d left)")

    send_message(chat_id, "\n".join(lines))


def send_weekly_report():
    """Every Sunday 8 PM — AI weekly report."""
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.summary import build_weekly_report

    chat_id = get_my_chat_id()
    report = build_weekly_report()
    send_message(chat_id, f"📊 *Weekly Report*\n\n{report}")


def reset_daily_overrides():
    with open("data/overrides.json", "w") as f:
        json.dump({"date": "", "classes": []}, f)
    print("[Scheduler] Daily overrides reset.")


def start_scheduler():
    tz = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    # Every minute — check for class reminders (10 min before)
    scheduler.add_job(send_class_reminders, "interval", minutes=1, id="class_reminders")

    # 8:00 AM — Daily summary + weather + escalation alerts
    scheduler.add_job(send_daily_summary, CronTrigger(hour=8, minute=0, timezone=tz), id="daily_summary")
    scheduler.add_job(send_escalation_reminders, CronTrigger(hour=8, minute=5, timezone=tz), id="escalation")

    # 8:00 PM — Evening deadline reminder
    scheduler.add_job(send_evening_reminder, CronTrigger(hour=20, minute=0, timezone=tz), id="evening_reminder")

    # Sunday 8:00 PM — Weekly report
    scheduler.add_job(send_weekly_report, CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=tz), id="weekly_report")

    # Midnight — Reset overrides
    scheduler.add_job(reset_daily_overrides, CronTrigger(hour=0, minute=0, timezone=tz), id="reset_overrides")

    scheduler.start()
    print("[Scheduler] Started — class reminders, daily summary, escalation, evening reminder, weekly report, override reset.")
