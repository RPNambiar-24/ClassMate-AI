import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "✅ WhatsApp Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "no data"}), 200

    type_webhook = data.get("typeWebhook", "")

    if type_webhook == "incomingMessageReceived":
        sender = data.get("senderData", {})
        chat_id = sender.get("chatId", "")
        my_phone = os.getenv("MY_PHONE", "")

        if my_phone and not chat_id.startswith(my_phone):
            return jsonify({"status": "ignored"}), 200

        message_data = data.get("messageData", {})
        msg_type = message_data.get("typeMessage", "")

        text = (
            message_data.get("textMessageData", {}).get("textMessage", "")
            or message_data.get("textMessageData", {}).get("textMessageBody", "")
            or message_data.get("extendedTextMessageData", {}).get("text", "")
            or ""
        )

        if msg_type in ("textMessage", "extendedTextMessage") and text:
            try:
                from bot_handler import handle_message
                handle_message(chat_id, text.strip())
            except Exception as e:
                print(f"[ERROR] handle_message failed: {e}")
                import traceback
                traceback.print_exc()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    from scheduler import start_scheduler
    start_scheduler()
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
