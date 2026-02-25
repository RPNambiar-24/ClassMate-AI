import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def ask_gemini(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Groq] ERROR: GROQ_API_KEY not set in .env")
        return "⚠️ AI summary unavailable — API key missing."
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq] Error: {e}")
        return "⚠️ AI summary unavailable right now."
