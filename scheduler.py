import os
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv
from data.db import get_conn

load_dotenv()
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")


def _get_all_chat_ids() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT chat_id FROM users").fetchall()
    conn.close()
    return [r["chat_id"] for r in rows]


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


def send_class_reminders():
    from utils.telegram_bot import send_message
    from commands.timetable import get_today_classes
    from commands.assignments import get_all_pending

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    reminder_time = (now + timedelta(minutes=10)).strftime("%H:%M")

    for chat_id in _get_all_chat_ids():
        _, classes = get_today_classes(chat_id)
        pending = get_all_pending(chat_id)

        for cls in classes:
            if cls.get("time", "") == reminder_time:
                msg = (
                    f"⏰ *Class Reminder!*\n"
                    f"📚 *{cls['subject']}* in 10 minutes at *{cls['time']}*\n"
                    f"Get ready! 🎒"
                )
                related = [p for p in pending if p["subject"].lower() == cls["subject"].lower()]
                if related:
                    item = related[0]
                    days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
                    msg += f"\n\n⚠️ Pending {'test' if item['type']=='test' else 'assignment'} due in *{days_left}d*."
                _run_async(send_message(chat_id, msg))


def send_daily_summaries():
    from utils.telegram_bot import send_message
    from commands.summary import build_daily_summary
    from data.db import get_user_name

    for chat_id in _get_all_chat_ids():
        name = get_user_name(chat_id)
        summary = build_daily_summary(chat_id)
        _run_async(send_message(chat_id, f"🌅 *Good Morning, {name}!*\n\n{summary}"))


def send_escalation_reminders():
    from utils.telegram_bot import send_message
    from commands.assignments import get_all_pending
    from commands.summary import build_escalation_message

    for chat_id in _get_all_chat_ids():
        for item in get_all_pending(chat_id):
            try:
                days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
                if days_left in [0, 1, 3, 7]:
                    msg = build_escalation_message(item, days_left)
                    _run_async(send_message(chat_id, msg))
            except Exception as e:
                print(f"[Scheduler] Escalation error: {e}")


def send_evening_reminders():
    from utils.telegram_bot import send_message
    from commands.assignments import get_due_soon

    for chat_id in _get_all_chat_ids():
        due_items = get_due_soon(chat_id, days=2)
        if not due_items:
            continue
        lines = ["📌 *Evening Deadline Check*\n"]
        for item in due_items:
            emoji = "📝" if item["type"] == "assignment" else "📋"
            days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
            urg = "🔴" if days_left <= 0 else "🟡" if days_left == 1 else "🟢"
            lines.append(f"{urg} {emoji} *{item['subject']}* — {item['due_date']} ({days_left}d left)")
        _run_async(send_message(chat_id, "\n".join(lines)))


def ask_saturday_timetable():
    from utils.telegram_bot import send_message

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday_date = (now + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")

    msg = (
        f"📅 *Saturday Schedule Check*\n\n"
        f"What timetable is Saturday ({saturday_date})?\n\n"
        f"Reply with:\n"
        f"  `/saturday Monday` — use Monday's timetable\n"
        f"  `/saturday holiday` — no classes 🎉\n"
        f"  `/saturday normal` — normal Saturday timetable"
    )
    for chat_id in _get_all_chat_ids():
        _run_async(send_message(chat_id, msg))


def reset_daily_overrides():
    conn = get_conn()
    conn.execute("DELETE FROM overrides")
    conn.commit()
    conn.close()
    print("[Scheduler] Daily overrides reset.")


def start_scheduler():
    tz = pytz.timezone(TIMEZONE)
    sched = BackgroundScheduler(timezone=tz)

    sched.add_job(send_class_reminders, "interval", minutes=1, id="class_reminders")
    sched.add_job(send_daily_summaries, CronTrigger(hour=8, minute=0, timezone=tz), id="daily_summary")
    sched.add_job(send_escalation_reminders, CronTrigger(hour=8, minute=5, timezone=tz), id="escalation")
    sched.add_job(send_evening_reminders, CronTrigger(hour=20, minute=0, timezone=tz), id="evening")
    sched.add_job(ask_saturday_timetable, CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=tz), id="saturday_check")
    sched.add_job(reset_daily_overrides, CronTrigger(hour=0, minute=0, timezone=tz), id="reset_overrides")

    sched.start()
    print("[Scheduler] Started.")
