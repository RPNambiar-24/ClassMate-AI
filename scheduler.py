import os
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv
from telegram import Bot
from data.db import get_conn, get_all_chat_ids

load_dotenv()
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

_bot = None
_main_loop = None


def set_main_loop(loop):
    global _main_loop
    _main_loop = loop


def get_bot():
    global _bot
    if _bot is None:
        _bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    return _bot


def send(chat_id, text):
    async def _send():
        try:
            await get_bot().send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            print(f"[Scheduler] Send error to {chat_id}: {e}")

    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(_send(), _main_loop)
    else:
        asyncio.run(_send())


def send_class_reminders():
    from commands.timetable import get_today_classes
    from commands.assignments import get_all_pending

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    reminder_time = (now + timedelta(minutes=10)).strftime("%H:%M")

    for chat_id in get_all_chat_ids():
        try:
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
                        days_left = (datetime.strptime(related[0]["due_date"], "%Y-%m-%d") - datetime.now()).days
                        msg += f"\n\n⚠️ Pending {'test' if related[0]['type']=='test' else 'assignment'} due in *{days_left}d*."
                    send(chat_id, msg)
        except Exception as e:
            print(f"[Scheduler] Reminder error for {chat_id}: {e}")


def send_daily_summaries():
    from commands.summary import build_daily_summary
    from data.db import get_user_name

    for chat_id in get_all_chat_ids():
        try:
            name = get_user_name(chat_id)
            summary = build_daily_summary(chat_id)
            send(chat_id, f"🌅 *Good Morning, {name}!*\n\n{summary}")
        except Exception as e:
            print(f"[Scheduler] Summary error for {chat_id}: {e}")


def send_escalation_reminders():
    from commands.assignments import get_all_pending
    from commands.summary import build_escalation_message

    for chat_id in get_all_chat_ids():
        for item in get_all_pending(chat_id):
            try:
                days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
                if days_left in [0, 1, 3, 7]:
                    send(chat_id, build_escalation_message(item, days_left))
            except Exception as e:
                print(f"[Scheduler] Escalation error: {e}")


def send_evening_reminders():
    from commands.assignments import get_due_soon

    for chat_id in get_all_chat_ids():
        try:
            due_items = get_due_soon(chat_id, days=2)
            if not due_items:
                continue
            lines = ["📌 *Evening Deadline Check*\n"]
            for item in due_items:
                emoji = "📝" if item["type"] == "assignment" else "📋"
                days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
                urg = "🔴" if days_left <= 0 else "🟡" if days_left == 1 else "🟢"
                lines.append(f"{urg} {emoji} *{item['subject']}* — {item['due_date']} ({days_left}d left)")
            send(chat_id, "\n".join(lines))
        except Exception as e:
            print(f"[Scheduler] Evening error for {chat_id}: {e}")


def ask_saturday_timetable():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    days_until_saturday = (5 - now.weekday()) % 7 or 7
    saturday_date = (now + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")
    msg = (
        f"📅 *Saturday Schedule Check*\n\n"
        f"What timetable is Saturday ({saturday_date})?\n\n"
        f"`/saturday Monday` — use Monday's timetable\n"
        f"`/saturday holiday` — no classes 🎉\n"
        f"`/saturday normal` — normal Saturday timetable"
    )
    for chat_id in get_all_chat_ids():
        try:
            send(chat_id, msg)
        except Exception as e:
            print(f"[Scheduler] Saturday check error for {chat_id}: {e}")


def reset_daily_overrides():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM overrides")
        conn.commit()
        cur.close()
        conn.close()
        print("[Scheduler] Daily overrides reset.")
    except Exception as e:
        print(f"[Scheduler] Override reset error: {e}")


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
