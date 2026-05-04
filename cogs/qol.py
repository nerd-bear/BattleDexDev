# Just to be clear QOL stand for quality of life, such as joining messages and other dumb things that make the user experience better but aren't core features of the bot

import disnake
from disnake.ext import commands

class Components(disnake.ui.LayoutView):    
    container1 = disnake.ui.Container(
        disnake.ui.TextDisplay(content="# Battle Dex is now here! Fuck yeah"),
        disnake.ui.MediaGallery(
            disnake.MediaGalleryItem(
                media="attachment://0f663482e9a64b46e77775806ca60479.png",
            ),
        ),
        disnake.ui.ActionRow(
                disnake.ui.Button(
                    style=disnake.ButtonStyle.primary,
                    label="Set channel",
                    emoji="🔩",
                    custom_id="cdc2a0083fcc4521e53f1bf21a83517f",
                ),
                disnake.ui.Button(
                    style=disnake.ButtonStyle.danger,
                    label="Delete Message",
                    emoji="🗑️",
                    custom_id="8aafdc13e964401dbaef2b26114708ec",
                ),
        ),
        accent_colour=disnake.Colour(9225410),
    )


class QoLCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        channel = None
        for ch in guild.text_channels:
            if ch.permissions_for(guild.default_role).send_messages:
                channel = ch
                break
        
        view = Components()
        await channel.send(view=view)

def setup(bot: commands.InteractionBot):
    bot.add_cog(QoLCog(bot))