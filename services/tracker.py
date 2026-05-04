import argparse
import os
import sys
import time
import requests
from collections import deque
from datetime import datetime
from fr24sdk.client import Client
from fr24sdk.exceptions import ApiError

# ==========================================
# RATE LIMITER SETUP
# ==========================================
class RateLimiter:
    """A sliding window rate limiter to prevent API bans."""
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def wait(self):
        """Blocks execution if the rate limit has been reached."""
        now = time.time()
        
        # Remove timestamps that are older than our time window (60 seconds)
        while self.calls and now - self.calls[0] >= self.period:
            self.calls.popleft()

        # If we've hit our limit, calculate how long to sleep
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                print(f"⏱️ Rate limit reached (10 req/min). Pausing for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        # Record the timestamp of this new request
        self.calls.append(time.time())

# Global instance: 10 requests per 60 seconds
global_limiter = RateLimiter(max_calls=10, period=60.0)


# ==========================================
# FLIGHT DATA FUNCTIONS
# ==========================================
def get_extended_flight_info(flight_id: str) -> dict:
    """
    Fetches the high-resolution JetPhotos image URL AND the full aircraft 
    model name using Flightradar24's internal web clickhandler endpoint.
    """
    result = {
        "image_url": "N/A",
        "aircraft_model": "N/A"
    }

    if not flight_id or flight_id == 'N/A':
        return result
        
    url = f"https://data-live.flightradar24.com/clickhandler/?version=1.5&flight={flight_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        # 🚦 Trigger Rate Limiter before the web request
        global_limiter.wait()
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        aircraft_data = data.get('aircraft', {})
        
        model_info = aircraft_data.get('model', {})
        result['aircraft_model'] = model_info.get('text', 'N/A')
        
        images = aircraft_data.get('images', {})
        large_images = images.get('large', [])
        if large_images:
            result['image_url'] = large_images[0].get('src', 'N/A')
            
    except Exception as e:
        pass
        
    return result


def get_flight_data(flight_identifier: str, api_token: str = None) -> list[dict]:
    target_flight = flight_identifier.upper()
    token = api_token or os.environ.get("FR24_API_TOKEN")
    
    if not token:
        raise ValueError("FR24_API_TOKEN is missing. Set it as an environment variable or pass it to the function.")

    processed_flights = []

    try:
        with Client(api_token=token) as client:
            
            # 🚦 Trigger Rate Limiter before SDK request
            global_limiter.wait()
            response = client.live.flight_positions.get_full(flights=[target_flight])
            flight_data = getattr(response, 'data', [])
            
            if not flight_data:
                # 🚦 Trigger Rate Limiter before fallback SDK request
                global_limiter.wait()
                response = client.live.flight_positions.get_full(callsigns=[target_flight])
                flight_data = getattr(response, 'data', [])

            if not flight_data:
                return processed_flights

            for f in flight_data:
                if hasattr(f, 'model_dump'):
                    raw_data = f.model_dump()
                elif hasattr(f, 'dict'):
                    raw_data = f.dict()
                else:
                    raw_data = vars(f)

                # vertical trend
                vspeed = raw_data.get('vspeed', 0)
                if isinstance(vspeed, (int, float)):
                    if vspeed > 0:
                        v_trend = f"Climbing (+{vspeed} ft/min)"
                    elif vspeed < 0:
                        v_trend = f"Descending ({vspeed} ft/min)"
                    else:
                        v_trend = "Level (0 ft/min)"
                else:
                    v_trend = "N/A"

                # time
                timestamp_str = raw_data.get('timestamp', '')
                try:
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except ValueError:
                    formatted_time = timestamp_str or "N/A"

                registration = raw_data.get('reg', 'N/A')
                flight_id = raw_data.get('fr24_id', 'N/A')
                
                # This function also has a rate limiter inside it!
                extended_info = get_extended_flight_info(flight_id)
                
                aircraft_model = extended_info['aircraft_model']
                if aircraft_model == 'N/A':
                    aircraft_model = raw_data.get('equip', 'N/A')

                processed_flights.append({
                    "callsign": raw_data.get('callsign', 'N/A'),
                    "registration": registration,
                    "aircraft_model": aircraft_model,
                    "latitude": raw_data.get('lat', 'N/A'),
                    "longitude": raw_data.get('lon', 'N/A'),
                    "altitude_ft": raw_data.get('alt', 0),
                    "vertical_speed_trend": v_trend,
                    "ground_speed_kts": raw_data.get('gspeed', 0),
                    "heading_deg": raw_data.get('track', 'N/A'),
                    "squawk": str(raw_data.get('squawk', 'N/A')).lstrip('0'),
                    "updated_at": formatted_time,
                    "image_url": extended_info['image_url'],
                    "raw_data": raw_data 
                })

            return processed_flights

    except ApiError as e:
        raise RuntimeError(f"Flightradar24 API Error: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(description="Fetch live flight info from Flightradar24.")
    parser.add_argument("flight_number", help="The flight number or callsign to search for (e.g., DL2204)")
    args = parser.parse_args()

    print(f"Searching for live data for: {args.flight_number}...")

    try:
        results = get_flight_data(args.flight_number)

        if not results:
            print(f"\nNo active live flights found matching '{args.flight_number}'.")
            return

        for data in results:
            print("\n" + "=" * 60)
            print(f" ✈️  FLIGHT: {data['callsign']} | REG: {data['registration']}")
            print(f" 🛫 AIRCRAFT: {data['aircraft_model']}")
            print("=" * 60)
            print(f"  🗺️ Position : {data['latitude']}, {data['longitude']}")
            print(f"  🗻 Altitude : {data['altitude_ft']:,} ft ({data['vertical_speed_trend']})")
            print(f"  💨 Speed    : {data['ground_speed_kts']} knots")
            print(f"  🧭 Heading  : {data['heading_deg']}°")
            print(f"  📜 Squawk   : {data['squawk']}")
            print(f"  🕛 Updated  : {data['updated_at']}")
            print(f"  📸 Image    : {data['image_url']}")
            print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()