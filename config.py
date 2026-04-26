import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

DB_PATH = os.getenv("DB_PATH", "sqlite:///pets.db")

YANDEX_GEOCODER_API_KEY = os.getenv("YANDEX_GEOCODER_API_KEY", "")

YANDEX_PLACES_API_KEY = os.getenv("YANDEX_PLACES_API_KEY", "")

YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY", "")
