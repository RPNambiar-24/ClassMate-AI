from utils.whatsapp import send_message
from commands.timetable import (
    view_timetable, add_class, remove_class,
    override_today, clear_override, set_saturday_override
)
from commands.assignments import (
    add_assignment, view_assignments, mark_done, delete_assignment
)
from commands.summary import build_daily_summary


HELP_TEXT = """
🤖 *WhatsApp Study Bot — Commands*

📅 *Timetable*
  !tt                    — Today's timetable
  !tt Monday             — Specific day
  !tt all                — Full week
  !add_class [Day] [HH:MM] [Subject]
  !remove_class [Day] [HH:MM]
  !override [HH:MM Subject, HH:MM Subject]
  !clear_override
  !saturday [Day/holiday/normal]

📝 *Assignments & Tests*
  !tasks                 — All pending
  !assignments           — Only assignments
  !tests                 — Only tests
  !add_assignment [Subject] [YYYY-MM-DD]
  !add_test [Subject] [YYYY-MM-DD]
  !done [#id]            — Mark as done
  !delete [#id]          — Delete item

🌅 *AI*
  !summary               — AI summary now

❓ !help                 — This menu
""".strip()


def handle_message(chat_id: str, text: str):
    if not text:
        return

    cmd = text.lower().strip()
    parts = text.strip().split()

    # HELP
    if cmd in ["!help", "help", "hi", "hello", "start"]:
        send_message(chat_id, HELP_TEXT)

    # TIMETABLE
    elif cmd == "!tt":
        from datetime import datetime
        day = datetime.now().strftime("%A")
        send_message(chat_id, view_timetable(day))

    elif cmd.startswith("!tt "):
        arg = text[4:].strip()
        send_message(chat_id, view_timetable() if arg.lower() == "all" else view_timetable(arg))

    elif cmd.startswith("!add_class "):
        args = text[11:].strip().split(" ", 2)
        if len(args) < 3:
            send_message(chat_id, "Usage: `!add_class [Day] [HH:MM] [Subject]`")
        else:
            send_message(chat_id, add_class(args[0], args[1], args[2]))

    elif cmd.startswith("!remove_class "):
        args = text[14:].strip().split(" ", 1)
        if len(args) < 2:
            send_message(chat_id, "Usage: `!remove_class [Day] [HH:MM]`")
        else:
            send_message(chat_id, remove_class(args[0], args[1]))

    elif cmd.startswith("!override "):
        send_message(chat_id, override_today(text[10:].strip()))

    elif cmd == "!clear_override":
        send_message(chat_id, clear_override())

    elif cmd.startswith("!saturday "):
        arg = text[10:].strip()
        send_message(chat_id, set_saturday_override(arg))

    # ASSIGNMENTS
    elif cmd == "!tasks":
        send_message(chat_id, view_assignments())

    elif cmd == "!assignments":
        send_message(chat_id, view_assignments("assignment"))

    elif cmd == "!tests":
        send_message(chat_id, view_assignments("test"))

    elif cmd.startswith("!add_assignment ") or cmd.startswith("!add_test "):
        is_test = cmd.startswith("!add_test")
        prefix = len("!add_test ") if is_test else len("!add_assignment ")
        args = text[prefix:].strip().split(" ", 1)
        if len(args) < 2:
            usage = "!add_test [Subject] [YYYY-MM-DD]" if is_test else "!add_assignment [Subject] [YYYY-MM-DD]"
            send_message(chat_id, f"Usage: `{usage}`")
        else:
            type_ = "test" if is_test else "assignment"
            send_message(chat_id, add_assignment(args[0], args[1], type_))

    elif cmd.startswith("!done "):
        try:
            item_id = int(text[6:].strip().replace("#", ""))
            send_message(chat_id, mark_done(item_id))
        except ValueError:
            send_message(chat_id, "Usage: `!done [id]` — e.g. `!done 3`")

    elif cmd.startswith("!delete "):
        try:
            item_id = int(text[8:].strip().replace("#", ""))
            send_message(chat_id, delete_assignment(item_id))
        except ValueError:
            send_message(chat_id, "Usage: `!delete [id]` — e.g. `!delete 3`")

    # AI SUMMARY
    elif cmd == "!summary":
        send_message(chat_id, "⏳ Generating your AI summary...")
        summary = build_daily_summary()
        send_message(chat_id, f"🌅 *Today's Summary*\n\n{summary}")

    # UNKNOWN
    else:
        send_message(chat_id, f"❓ Unknown command: *{parts[0]}*\nType *!help* to see all commands.")
