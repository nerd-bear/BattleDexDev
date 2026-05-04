from datetime import datetime

import disnake
from disnake.ext import commands

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
        # 1. Fetch the data
        # Since this involves a blocking web request (requests.get and time.sleep),
        # it's best practice to defer the response so the interaction doesn't fail
        # if the rate limiter pauses for a few seconds.
        await inter.response.defer() 
        
        results = get_flight_data(flight_number)
        
        # 2. Check if we actually found anything
        if not results:
            await inter.edit_original_response(content=f"No active live flights found matching `{flight_number}`.")
            return
            
        # 3. Grab the FIRST flight in the returned list
        flight = results[0] 

        # 4. Extract data from the dictionary
        callsign = flight['callsign']
        registration = flight['registration']
        aircraft_model = flight['aircraft_model']
        latitude = flight['latitude']
        longitude = flight['longitude']
        altitude = flight['altitude_ft']
        vertical_speed_trend = flight['vertical_speed_trend']
        ground_speed = flight['ground_speed_kts']
        heading = flight['heading_deg']
        squawk = flight['squawk']
        updated_at = flight['updated_at']
        image_url = flight['image_url']
        
        # 5. Build the embed
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

        if image_url != "N/A":
            embed.set_image(url=image_url)

        embed.set_footer(text="Data Provided by FlightRadar24",
                        icon_url="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/webp/flightradar24-light.webp")
        
        # 6. Send the result using edit_original_response because we deferred earlier
        await inter.edit_original_response(embed=embed)