import os
from dotenv import load_dotenv

load_dotenv("/home/battledex/BattleDexDev/.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = "cards.db"
CARD_FILE = "data/card.json"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")