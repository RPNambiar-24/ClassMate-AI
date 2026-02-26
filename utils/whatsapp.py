import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_message(chat_id: str, text: str):
    instance_id = os.getenv("GREEN_API_INSTANCE_ID")
    token = os.getenv("GREEN_API_TOKEN")
    url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{token}"
    payload = {"chatId": chat_id, "message": text}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"[WhatsApp] Sent to {chat_id}: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"[WhatsApp] Send error: {e}")
        return {}

def get_my_chat_id() -> str:
    phone = os.getenv("MY_PHONE", "")
    return f"{phone}@c.us"
