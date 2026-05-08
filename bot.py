import disnake
from disnake.ext import commands

from cogs.fl24 import FL24Cog
from cogs.qol import QoLCog
from config import BOT_TOKEN, DATABASE_PATH, CARD_FILE
from database import Database
from cogs.cards import CardsCog


intents = disnake.Intents.default()
intents.members = True
bot = commands.InteractionBot(intents=intents)

db = Database(DATABASE_PATH)


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")


def main():
    db.initialize()
    db.seed_from_json(CARD_FILE)
    bot.add_cog(CardsCog(bot, db))
    bot.add_cog(FL24Cog(bot))
    bot.add_cog(QoLCog(bot))
    bot.run(BOT_TOKEN)
    


if __name__ == "__main__":
    main()