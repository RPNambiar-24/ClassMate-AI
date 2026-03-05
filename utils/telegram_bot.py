import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

_bot = None

def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    return _bot

async def send_message(chat_id: int, text: str, reply_markup=None):
    bot = get_bot()
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

