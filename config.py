import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

DB_PATH = os.getenv("DB_PATH", "sqlite:///pets.db")

YANDEX_GEOCODER_API_KEY = os.getenv("YANDEX_GEOCODER_API_KEY", "")

YANDEX_PLACES_API_KEY = os.getenv("YANDEX_PLACES_API_KEY", "")

YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY", "")

# Адрес локального AI-сервера.
AI_SERVER_URL = "http://127.0.0.1:8000/v1/chat/completions"

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-20b")

AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "180"))

AI_SYSTEM_PROMPT = os.getenv(
    "AI_SYSTEM_PROMPT",
    "Ты дружелюбный помощник внутри Telegram-бота о питомцах. Отвечай на русском языке просто и понятно. Если вопрос связан со здоровьем животного и есть тревожные симптомы, советуй обратиться к ветеринару.",
)
