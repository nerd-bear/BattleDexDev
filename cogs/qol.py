import disnake
from disnake.ext import commands

# 1. Standard disnake View for your buttons
class Components(disnake.ui.View):
    def __init__(self):
        # timeout=None ensures the buttons don't stop working after 3 minutes
        super().__init__(timeout=None)
        
        # Add the "Set channel" button
        self.add_item(disnake.ui.Button(
            style=disnake.ButtonStyle.primary,
            label="Set channel",
            emoji="🔩",
            custom_id="cdc2a0083fcc4521e53f1bf21a83517f"
        ))
        
        # Add the "Delete Message" button
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
        # Find the first channel the bot can speak in
        channel = None
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages: # Note: checked against bot's perms, not default_role
                channel = ch
                break
        
        if channel is None:
            return # Nowhere to send the message!

        # 2. Build the Embed for your text and color
        embed = disnake.Embed(
            description="# Battle Dex is now here! Fuck yeah",
            color=disnake.Colour(9225410) # Your accent color
        )

        # 3. Handle the image attachment
        # Make sure the file is actually on your machine at this path
        file_path = "assets/promotional/promo_banner_alpha.png" 
        try:
            image_file = disnake.File(file_path, filename="battledex.png")
            embed.set_image(url="attachment://battledex.png")
        except FileNotFoundError:
            image_file = None # Failsafe in case the image isn't found
            print("Warning: Join image not found.")

        # 4. Initialize the view and send everything
        view = Components()
        
        if image_file:
            await channel.send(embed=embed, file=image_file, view=view)
        else:
            await channel.send(embed=embed, view=view)

def setup(bot: commands.InteractionBot):
    bot.add_cog(QoLCog(bot))