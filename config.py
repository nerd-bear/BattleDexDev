import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = ""
DATABASE_PATH = "cards.db"
CARD_FILE = "data/card.json"
MAIN_GUILD_ID = 1495045506429227178  
if not BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set.")