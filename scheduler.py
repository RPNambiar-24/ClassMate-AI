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
    pending = get_all_pending()

    for cls in classes:
        cls_time = cls.get("time", cls.get("start", ""))
        if cls_time == reminder_time:
            msg = (
                f"⏰ *Class Reminder!*\n"
                f"📚 *{cls['subject']}* in 10 minutes at *{cls_time}*.\n"
                f"Get ready! 🎒"
            )
            related = [p for p in pending if p["subject"].lower() == cls["subject"].lower()]
            if related:
                item = related[0]
                days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
                msg += (
                    f"\n\n⚠️ Pending {'test' if item['type'] == 'test' else 'assignment'} "
                    f"for this subject due in *{days_left}d*."
                )
            send_message(chat_id, msg)


def send_daily_summary():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.summary import build_daily_summary

    chat_id = get_my_chat_id()
    summary = build_daily_summary()
    send_message(chat_id, f"🌅 *Good Morning, Rishab!*\n\n{summary}")


def send_escalation_reminders():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.assignments import get_all_pending
    from commands.summary import build_escalation_message

    chat_id = get_my_chat_id()
    pending = get_all_pending()

    for item in pending:
        try:
            due = datetime.strptime(item["due_date"], "%Y-%m-%d")
            days_left = (due - datetime.now()).days
            if days_left in [0, 1, 3, 7]:
                msg = build_escalation_message(item, days_left)
                send_message(chat_id, msg)
        except Exception as e:
            print(f"[Scheduler] Escalation error: {e}")


def send_evening_reminder():
    from utils.whatsapp import send_message, get_my_chat_id
    from commands.assignments import get_due_soon

    due_items = get_due_soon(days=2)
    if not due_items:
        return

    chat_id = get_my_chat_id()
    lines = ["📌 *Evening Deadline Check*\n"]
    for item in due_items:
        emoji = "📝" if item["type"] == "assignment" else "📋"
        days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
        urg = "🔴" if days_left <= 0 else "🟡" if days_left == 1 else "🟢"
        lines.append(f"{urg} {emoji} *{item['subject']}* — {item['due_date']} ({days_left}d left)")
    send_message(chat_id, "\n".join(lines))


def ask_saturday_timetable():
    from utils.whatsapp import send_message, get_my_chat_id

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday_date = (now + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")

    msg = (
        f"📅 *Saturday Schedule Check*\n\n"
        f"What timetable is this Saturday ({saturday_date})?\n\n"
        f"Reply with:\n"
        f"  • `!saturday Monday` — use Monday's timetable\n"
        f"  • `!saturday Tuesday` — use Tuesday's timetable\n"
        f"  • `!saturday Wednesday` — use Wednesday's timetable\n"
        f"  • `!saturday Thursday` — use Thursday's timetable\n"
        f"  • `!saturday Friday` — use Friday's timetable\n"
        f"  • `!saturday holiday` — no classes 🎉\n"
        f"  • `!saturday normal` — use normal Saturday timetable"
    )
    send_message(get_my_chat_id(), msg)


def reset_daily_overrides():
    with open("data/overrides.json", "w") as f:
        json.dump({"date": "", "classes": []}, f)
    print("[Scheduler] Overrides reset.")


def start_scheduler():
    tz = pytz.timezone(TIMEZONE)
    sched = BackgroundScheduler(timezone=tz)

    # Every minute — class reminders
    sched.add_job(send_class_reminders, "interval", minutes=1, id="class_reminders")

    # 8:00 AM — Daily summary
    sched.add_job(send_daily_summary, CronTrigger(hour=8, minute=0, timezone=tz), id="daily_summary")

    # 8:05 AM — Escalation alerts
    sched.add_job(send_escalation_reminders, CronTrigger(hour=8, minute=5, timezone=tz), id="escalation")

    # 8:00 PM — Evening deadline check
    sched.add_job(send_evening_reminder, CronTrigger(hour=20, minute=0, timezone=tz), id="evening")

    # Sunday 8:00 PM — Ask about Saturday timetable
    sched.add_job(
        ask_saturday_timetable,
        CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=tz),
        id="saturday_check"
    )

    # Midnight — Reset daily overrides
    sched.add_job(reset_daily_overrides, CronTrigger(hour=0, minute=0, timezone=tz), id="reset_overrides")

    sched.start()
    print("[Scheduler] Started.")
