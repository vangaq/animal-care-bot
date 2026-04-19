import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = "8445913049:AAF2b0viRLRhkdZaG-LedYCC3VWKMYN0Agc"
DB_PATH = os.getenv("DB_PATH", "sqlite:///pets.db")
