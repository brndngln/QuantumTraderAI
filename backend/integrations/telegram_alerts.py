
import httpx
from backend.config.settings import settings

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    httpx.post(url, json=payload)
