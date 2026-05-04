import io
import requests
from datetime import datetime

import disnake
from disnake.ext import commands

# Assuming you still need your database import for future use
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
        # 1. Defer the response because scraping/downloading might take longer than 3 seconds
        await inter.response.defer() 
        
        results = get_flight_data(flight_number)
        
        # 2. Handle no results
        if not results:
            await inter.edit_original_response(content=f"No active live flights found matching `{flight_number}`.")
            return
            
        # 3. Grab the FIRST flight in the returned list
        flight = results[0] 

        # 4. Extract data
        callsign = flight['callsign']
        registration = flight['registration']
        aircraft_model = flight['aircraft_model']
        latitude = flight['latitude']
        longitude = flight['longitude']
        altitude = flight['altitude_ft']
        vertical_speed_trend = flight['vertical_speed_trend']
        
        # Using .get() here just in case you named it ground_speed_kts or gnd_speed_kts
        ground_speed = flight.get('gnd_speed_kts', flight.get('ground_speed_kts', 0)) 
        
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

        embed.set_footer(text="Data Provided by FlightRadar24",
                        icon_url="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/webp/flightradar24-light.webp")
        
        # 6. Image Handling (Bypass JetPhotos Hotlink Protection)
        print(f"--- DEBUG: Image URL from scraper: {image_url} ---")
        
        if image_url != "N/A":
            try:
                # We need a much stronger disguise to fool Cloudflare
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Referer': 'https://www.flightradar24.com/', # Tell JetPhotos we came from FR24
                }
                
                print("--- DEBUG: Attempting to download image... ---")
                # Increased timeout to 10s just in case Discord or JetPhotos is being slow
                img_response = requests.get(image_url, headers=headers, timeout=10) 
                
                print(f"--- DEBUG: Download status code: {img_response.status_code} ---")
                img_response.raise_for_status()
                
                # Save raw image data into memory
                image_bytes = io.BytesIO(img_response.content)
                discord_file = disnake.File(fp=image_bytes, filename="aircraft.jpg")
                
                # Attach to embed
                embed.set_image(url="attachment://aircraft.jpg")
                
                # Send both embed and file
                await inter.edit_original_response(embed=embed, file=discord_file)
                print("--- DEBUG: Image successfully attached and sent! ---")
                return
                
            except Exception as e:
                print(f"--- DEBUG: Image download FAILED: {e} ---")
                # Fallback: Send embed without image if download fails
                await inter.edit_original_response(embed=embed)
                return

        # 7. Send standard embed if no image exists
        await inter.edit_original_response(embed=embed) 


def setup(bot: commands.InteractionBot):
    bot.add_cog(FL24Cog(bot))