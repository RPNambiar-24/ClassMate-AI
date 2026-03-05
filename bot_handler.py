import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data.db import is_registered, register_user, get_user_name
from commands.timetable import (
    view_timetable, add_class, remove_class,
    override_today, clear_override, set_saturday_override, import_timetable
)
from commands.assignments import (
    add_assignment, view_assignments, mark_done, delete_assignment
)
from commands.summary import build_daily_summary, build_weekly_report


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Today's Timetable", callback_data="tt_today"),
         InlineKeyboardButton("📅 Full Week", callback_data="tt_all")],
        [InlineKeyboardButton("📝 Assignments", callback_data="view_assignments"),
         InlineKeyboardButton("📋 Tests", callback_data="view_tests")],
        [InlineKeyboardButton("📌 All Tasks", callback_data="view_tasks"),
         InlineKeyboardButton("🌅 AI Summary", callback_data="summary")],
        [InlineKeyboardButton("📊 Weekly Report", callback_data="weekly")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name or "Student"

    if not is_registered(chat_id):
        register_user(chat_id, name)
        await update.message.reply_text(
            f"👋 Welcome to *ClassMate AI*, {name}!\n\n"
            f"I'm your personal academic assistant. I'll remind you about classes, "
            f"track assignments, and send you AI-powered daily summaries.\n\n"
            f"*To get started, import your timetable:*\n"
            f"Send a JSON file of your timetable or use `/addclass` to add classes manually.\n\n"
            f"Type /help to see all commands.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"👋 Welcome back, *{name}*!",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *ClassMate AI — Commands*

📅 *Timetable*
  /tt — Today's timetable
  /tt Monday — Specific day
  /tt all — Full week
  /addclass Day HH:MM Subject
  /removeclass Day HH:MM
  /override HH:MM Subject, HH:MM Subject
  /clearoverride
  /saturday Day|holiday|normal

📝 *Assignments & Tests*
  /tasks — All pending
  /assignments — Only assignments
  /tests — Only tests
  /addassignment Subject YYYY-MM-DD
  /addtest Subject YYYY-MM-DD
  /done id — Mark as done
  /delete id — Delete item

🌅 *AI*
  /summary — AI summary now
  /weekly — Weekly report

📁 *Import*
  Send a JSON file — auto-imports timetable

❓ /help — This menu
""".strip()
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if not is_registered(chat_id):
        register_user(chat_id, update.effective_user.first_name or "Student")

    await update.message.reply_text("❓ Use /help to see all commands.", parse_mode="Markdown")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle JSON file upload for timetable import."""
    chat_id = update.effective_chat.id
    doc = update.message.document

    if not doc.file_name.endswith(".json"):
        await update.message.reply_text("❌ Please send a *.json* file.", parse_mode="Markdown")
        return

    file = await context.bot.get_file(doc.file_id)
    content = await file.download_as_bytearray()

    try:
        timetable_data = json.loads(content.decode("utf-8"))
        result = import_timetable(chat_id, timetable_data)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid JSON: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    await query.answer()

    if data == "tt_today":
        from datetime import datetime
        day = datetime.now().strftime("%A")
        await query.message.reply_text(view_timetable(chat_id, day), parse_mode="Markdown")

    elif data == "tt_all":
        await query.message.reply_text(view_timetable(chat_id), parse_mode="Markdown")

    elif data == "view_tasks":
        await query.message.reply_text(view_assignments(chat_id), parse_mode="Markdown")

    elif data == "view_assignments":
        await query.message.reply_text(view_assignments(chat_id, "assignment"), parse_mode="Markdown")

    elif data == "view_tests":
        await query.message.reply_text(view_assignments(chat_id, "test"), parse_mode="Markdown")

    elif data == "summary":
        await query.message.reply_text("⏳ Generating summary...", parse_mode="Markdown")
        summary = build_daily_summary(chat_id)
        await query.message.reply_text(f"🌅 *Today's Summary*\n\n{summary}", parse_mode="Markdown")

    elif data == "weekly":
        await query.message.reply_text("⏳ Generating weekly report...", parse_mode="Markdown")
        report = build_weekly_report(chat_id)
        await query.message.reply_text(f"📊 *Weekly Report*\n\n{report}", parse_mode="Markdown")


# ---- Individual command handlers ----

async def cmd_tt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    arg = " ".join(context.args) if context.args else None
    if not arg:
        from datetime import datetime
        arg = datetime.now().strftime("%A")
    await update.message.reply_text(view_timetable(chat_id, arg), parse_mode="Markdown")


async def cmd_addclass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: `/addclass Day HH:MM Subject`", parse_mode="Markdown")
        return
    result = add_class(chat_id, args[0], args[1], " ".join(args[2:]))
    await update.message.reply_text(result, parse_mode="Markdown")


async def cmd_removeclass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/removeclass Day HH:MM`", parse_mode="Markdown")
        return
    await update.message.reply_text(remove_class(chat_id, args[0], args[1]), parse_mode="Markdown")


async def cmd_override(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    await update.message.reply_text(override_today(chat_id, text), parse_mode="Markdown")


async def cmd_clearoverride(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(clear_override(update.effective_chat.id), parse_mode="Markdown")


async def cmd_saturday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    arg = " ".join(context.args) if context.args else ""
    await update.message.reply_text(set_saturday_override(chat_id, arg), parse_mode="Markdown")


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(view_assignments(update.effective_chat.id), parse_mode="Markdown")


async def cmd_assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(view_assignments(update.effective_chat.id, "assignment"), parse_mode="Markdown")


async def cmd_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(view_assignments(update.effective_chat.id, "test"), parse_mode="Markdown")


async def cmd_addassignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/addassignment Subject YYYY-MM-DD`", parse_mode="Markdown")
        return
    await update.message.reply_text(add_assignment(chat_id, args[0], args[1], "assignment"), parse_mode="Markdown")


async def cmd_addtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/addtest Subject YYYY-MM-DD`", parse_mode="Markdown")
        return
    await update.message.reply_text(add_assignment(chat_id, args[0], args[1], "test"), parse_mode="Markdown")


async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        item_id = int(context.args[0].replace("#", ""))
        await update.message.reply_text(mark_done(chat_id, item_id), parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/done id` — e.g. `/done 3`", parse_mode="Markdown")


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        item_id = int(context.args[0].replace("#", ""))
        await update.message.reply_text(delete_assignment(chat_id, item_id), parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/delete id` — e.g. `/delete 3`", parse_mode="Markdown")


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Generating summary...", parse_mode="Markdown")
    summary = build_daily_summary(chat_id)
    await update.message.reply_text(f"🌅 *Today's Summary*\n\n{summary}", parse_mode="Markdown")


async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Generating weekly report...", parse_mode="Markdown")
    report = build_weekly_report(chat_id)
    await update.message.reply_text(f"📊 *Weekly Report*\n\n{report}", parse_mode="Markdown")
