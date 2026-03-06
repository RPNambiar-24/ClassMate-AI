import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from data.db import init_db
from scheduler import start_scheduler, set_main_loop
import bot_handler as bh

load_dotenv()

def main():
    init_db()

    loop = asyncio.get_event_loop()
    set_main_loop(loop)
    start_scheduler()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", bh.start))
    app.add_handler(CommandHandler("help", bh.help_command))
    app.add_handler(CommandHandler("tt", bh.cmd_tt))
    app.add_handler(CommandHandler("addclass", bh.cmd_addclass))
    app.add_handler(CommandHandler("removeclass", bh.cmd_removeclass))
    app.add_handler(CommandHandler("override", bh.cmd_override))
    app.add_handler(CommandHandler("clearoverride", bh.cmd_clearoverride))
    app.add_handler(CommandHandler("saturday", bh.cmd_saturday))
    app.add_handler(CommandHandler("tasks", bh.cmd_tasks))
    app.add_handler(CommandHandler("assignments", bh.cmd_assignments))
    app.add_handler(CommandHandler("tests", bh.cmd_tests))
    app.add_handler(CommandHandler("addassignment", bh.cmd_addassignment))
    app.add_handler(CommandHandler("addtest", bh.cmd_addtest))
    app.add_handler(CommandHandler("done", bh.cmd_done))
    app.add_handler(CommandHandler("delete", bh.cmd_delete))
    app.add_handler(CommandHandler("summary", bh.cmd_summary))
    app.add_handler(CommandHandler("weekly", bh.cmd_weekly))
    app.add_handler(CommandHandler("dashboard", bh.cmd_dashboard))

    app.add_handler(CallbackQueryHandler(bh.button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, bh.handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bh.handle_text))

    async def post_init(application):
        set_main_loop(asyncio.get_event_loop())

    app.post_init = post_init

    print("🤖 ClassMate AI is running...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )

if __name__ == "__main__":
    main()
