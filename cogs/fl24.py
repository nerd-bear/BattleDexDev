from datetime import datetime

import disnake
from disnake.ext import commands

from database import Database
from services.tracker import get_flight_data


class FL24Cog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name="fl24",
        description="Main command for Flight Radar 24 features."
    )
    async def fl24(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @fl24.sub_command(name="track", description="Display information about a flight.")
    async def track(
        self,
        inter: disnake.ApplicationCommandInteraction,
        flight_number: str = commands.Param(
            description="Enter a flight number",
        )
    ):
        results = get_flight_data(flight_number)
        callsign = results['callsign']
        registration = results['registration']
        aircraft_model = results['aircraft_model']
        latitude = results['latitude']
        longitude = results['longitude']
        altitude = results['altitude_ft']
        vertical_speed_trend = results['vertical_speed_trend']
        ground_speed = results['ground_speed_kts']
        heading = results['heading_deg']
        squawk = results['squawk']
        updated_at = results['updated_at']
        image_url = results['image_url']
        
        embed = disnake.Embed(description=f"**{aircraft_model}** | REG: **{registration}**",
                            colour=0x303030,
                            timestamp=datetime.now())

        embed.set_author(name=f"Tracking Data for Flight {callsign}")

        embed.add_field(name="Position :",
                        value=f"Lat: {latitude}, Lng: {longitude}",
                        inline=True)
        embed.add_field(name="Altitude :",
                        value=f"{altitude} ft ({vertical_speed_trend})",
                        inline=True)
        embed.add_field(name="Speed :",
                        value=f"GND: {ground_speed} kts",
                        inline=True)
        embed.add_field(name="Heading :",
                        value=f"{heading}°",
                        inline=True)
        embed.add_field(name="Squawk :",
                        value=f"{squawk}",
                        inline=True)
        embed.add_field(name="Updated :",
                        value=f"{updated_at}",
                        inline=True)

        embed.set_image(url=image_url)

        embed.set_footer(text="Data Provided by FlightRadar24",
                        icon_url="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/webp/flightradar24-light.webp")
        
        inter.response.send_message(embed=embed)