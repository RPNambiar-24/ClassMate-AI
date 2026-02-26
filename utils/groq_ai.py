import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def ask_ai(prompt: str, max_tokens: int = 500) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Groq] ERROR: GROQ_API_KEY not set in .env")
        return "⚠️ AI unavailable — API key missing."
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq] Error: {e}")
        return "⚠️ AI unavailable right now."
