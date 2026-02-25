from utils.whatsapp import send_message
from commands.timetable import (
    view_timetable, add_class, remove_class, override_today, clear_override
)
from commands.assignments import (
    add_assignment, view_assignments, mark_done
)
from commands.summary import build_daily_summary


HELP_TEXT = """
🤖 *WhatsApp Study Bot — Commands*

📅 *Timetable*
  !tt              — Today's timetable
  !tt Monday       — Specific day's timetable
  !tt all          — Full week timetable
  !add_class [Day] [HH:MM] [Subject]
  !remove_class [Day] [HH:MM]
  !override [HH:MM Subject, HH:MM Subject, ...]
  !clear_override  — Restore normal timetable

📝 *Assignments & Tests*
  !tasks           — All upcoming tasks
  !assignments     — Only assignments
  !tests           — Only tests
  !add_assignment [Subject] [Title] [YYYY-MM-DD]
  !add_test [Subject] [Title] [YYYY-MM-DD]
  !done [#id]      — Mark task as done

🌅 *Summary*
  !summary         — Get AI summary now

❓ !help           — Show this menu
""".strip()


def handle_message(chat_id: str, text: str):
    if not text:
        return

    cmd = text.lower().strip()
    parts = text.strip().split()

    # ---------- HELP ----------
    if cmd in ["!help", "help", "hi", "hello", "start"]:
        send_message(chat_id, HELP_TEXT)

    # ---------- TIMETABLE ----------
    elif cmd == "!tt":
        from datetime import datetime
        day = datetime.now().strftime("%A")
        send_message(chat_id, view_timetable(day))

    elif cmd.startswith("!tt "):
        arg = text[4:].strip()
        if arg.lower() == "all":
            send_message(chat_id, view_timetable())
        else:
            send_message(chat_id, view_timetable(arg))

    elif cmd.startswith("!add_class "):
        # !add_class Monday 09:00 Mathematics
        args = text[11:].strip().split(" ", 2)
        if len(args) < 3:
            send_message(chat_id, "Usage: !add_class [Day] [HH:MM] [Subject]")
        else:
            send_message(chat_id, add_class(args[0], args[1], args[2]))

    elif cmd.startswith("!remove_class "):
        args = text[14:].strip().split(" ", 1)
        if len(args) < 2:
            send_message(chat_id, "Usage: !remove_class [Day] [HH:MM]")
        else:
            send_message(chat_id, remove_class(args[0], args[1]))

    elif cmd.startswith("!override "):
        classes_str = text[10:].strip()
        send_message(chat_id, override_today(classes_str))

    elif cmd == "!clear_override":
        send_message(chat_id, clear_override())

    # ---------- ASSIGNMENTS ----------
    elif cmd == "!tasks":
        send_message(chat_id, view_assignments())

    elif cmd == "!assignments":
        send_message(chat_id, view_assignments(filter_type="assignment"))

    elif cmd == "!tests":
        send_message(chat_id, view_assignments(filter_type="test"))

    elif cmd.startswith("!add_assignment ") or cmd.startswith("!add_test "):
        is_test = cmd.startswith("!add_test")
        prefix_len = len("!add_test ") if is_test else len("!add_assignment ")
        args = text[prefix_len:].strip().split(" ", 2)
        if len(args) < 3:
            send_message(chat_id, f"Usage: !add_{'test' if is_test else 'assignment'} [Subject] [Title] [YYYY-MM-DD]")
        else:
            type_ = "test" if is_test else "assignment"
            send_message(chat_id, add_assignment(args[0], args[1], args[2], type_=type_))

    elif cmd.startswith("!done "):
        try:
            item_id = int(text[6:].strip().replace("#", ""))
            send_message(chat_id, mark_done(item_id))
        except ValueError:
            send_message(chat_id, "Usage: !done [#id] — e.g., !done 3")

    # ---------- SUMMARY ----------
    elif cmd == "!summary":
        send_message(chat_id, "⏳ Generating your AI summary...")
        summary = build_daily_summary()
        send_message(chat_id, f"🌅 *Today's Summary*\n\n{summary}")

    # ---------- UNKNOWN ----------
    else:
        send_message(chat_id, f"❓ Unknown command: *{parts[0]}*\nType *!help* to see all commands.")
