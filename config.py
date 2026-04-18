import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = ""
DATABASE_PATH = "cards.db"
CARD_FILE = "data/card.json"
if not BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set.")