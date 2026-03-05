import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather() -> str:
    api_key = os.getenv("WEATHER_API_KEY")
    city = os.getenv("CITY", "Coimbatore")
    if not api_key:
        return ""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        desc = data["weather"][0]["description"].capitalize()
        hum = data["main"]["humidity"]
        return (
            f"🌤️ *{city} Weather*\n"
            f"  {desc}, {temp}°C (feels {feels}°C)\n"
            f"  💧 Humidity: {hum}%"
        )
    except Exception as e:
        print(f"[Weather] Error: {e}")
        return ""
