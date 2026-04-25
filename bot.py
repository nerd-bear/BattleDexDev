import disnake
from disnake.ext import commands

from config import BOT_TOKEN, DATABASE_PATH, CARD_FILE
from database import Database
from cogs.cards import CardsCog


intents = disnake.Intents.default()
bot = commands.InteractionBot(intents=intents)

db = Database(DATABASE_PATH)


@bot.event
async def on_ready():
    guild_ids = [guild.id for guild in bot.guilds]
    await bot.sync_commands(guild_ids=guild_ids)
    print(f"Bot is online as {bot.user}")


def main():
    db.initialize()
    db.seed_from_json(CARD_FILE)
    bot.add_cog(CardsCog(bot, db))
    bot.run(BOT_TOKEN)
    


if __name__ == "__main__":
    main()