import disnake
from disnake.ext import commands

class Components(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.add_item(disnake.ui.Button(
            style=disnake.ButtonStyle.primary,
            label="Set channel",
            emoji="🔩",
            custom_id="cdc2a0083fcc4521e53f1bf21a83517f"
        ))
        
        self.add_item(disnake.ui.Button(
            style=disnake.ButtonStyle.danger,
            label="Delete Message",
            emoji="🗑️",
            custom_id="8aafdc13e964401dbaef2b26114708ec"
        ))

class QoLCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        channel = None
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break
        
        if channel is None:
            return 

        embed = disnake.Embed(
            description="# Battle Dex is now here! Fuck yeah",
            color=disnake.Colour(9225410) 
        )

        file_path = "./assets/promotional/promo_banner_alpha.png" 
        try:
            image_file = disnake.File(file_path, filename="battledex.png")
            embed.set_image(url="attachment://battledex.png")
        except FileNotFoundError:
            image_file = None
            print("Warning: Join image not found.")

        view = Components()
        
        if image_file:
            await channel.send(embed=embed, file=image_file, view=view)
        else:
            await channel.send(embed=embed, view=view)

def setup(bot: commands.InteractionBot):
    bot.add_cog(QoLCog(bot))