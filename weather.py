import requests
from datetime import datetime
import os
import time
from typing import Dict, Any
import re

# ANSI color codes for terminal output
COLORS = {
    'BLUE': '\033[94m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'PURPLE': '\033[95m',
    'CYAN': '\033[96m',
    'BOLD': '\033[1m',
    'END': '\033[0m',
    'ORANGE': '\033[38;5;208m',
    'LIGHT_BLUE': '\033[38;5;39m',
    'DARK_BLUE': '\033[38;5;27m',
    'GRAY': '\033[38;5;245m'
}

# Enhanced ASCII art collection
WEATHER_ASCII = {
    'clear_day': f"""{COLORS['YELLOW']}
       \\   /
    __ /---\\__
   /  /-()-)  \\
   \\__/----\\__/
      /   \\{COLORS['END']}""",

    'clear_night': f"""{COLORS['DARK_BLUE']}
       *  .  
   .  *  .  *
     ___====___
  * (   moon  ) .
    \\_________/
   .   *   .{COLORS['END']}""",

    'cloudy': f"""{COLORS['GRAY']}
      .--.
   .-(    ).
  (___.__)__)
    -------
   -------{COLORS['END']}""",

    'rain_light': f"""{COLORS['CYAN']}
     .-.
    (   ).
   (___(__)
    ' ' ' '
   ' ' ' '{COLORS['END']}""",

    'rain_heavy': f"""{COLORS['BLUE']}
     .-.
    (   ).    
   (___(__) 
  ''' ''' '''  
 ''' ''' '''{COLORS['END']}""",

    'snow': f"""{COLORS['CYAN']}
     .-.
    (   ).
   (___(__)
    *  *  *
   *  *  *{COLORS['END']}""",

    'thunderstorm': f"""{COLORS['YELLOW']}
     .-.
    (   ).
   (___(__)
  ⚡'⚡'⚡'⚡
  '⚡'⚡'⚡'{COLORS['END']}""",

    'fog': f"""{COLORS['PURPLE']}
     .-.
  .-(    ).
 (___.__)__)
 =========
=========={COLORS['END']}"""
}

def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_weather_email(recipient: str, weather_report: str) -> bool:
    """Send weather report via email using resend.com API."""
    try:
        # Convert ANSI color codes to HTML
        html_report = weather_report.replace('\033[94m', '<span style="color: #3498db;">')  # Blue
        html_report = html_report.replace('\033[92m', '<span style="color: #2ecc71;">')     # Green
        html_report = html_report.replace('\033[93m', '<span style="color: #f1c40f;">')     # Yellow
        html_report = html_report.replace('\033[91m', '<span style="color: #e74c3c;">')     # Red
        html_report = html_report.replace('\033[95m', '<span style="color: #9b59b6;">')     # Purple
        html_report = html_report.replace('\033[96m', '<span style="color: #1abc9c;">')     # Cyan
        html_report = html_report.replace('\033[1m', '<strong>')                            # Bold
        html_report = html_report.replace('\033[0m', '</span>')                             # End color
        html_report = html_report.replace('\n', '<br>')                                     # Newlines

        # Create HTML email content
        # Note: The following HTML is simplified and may not work with all email clients
        html_content = f"""
        <html>
            <body style="font-family: monospace; white-space: pre;">
                {html_report}
            </body>
        </html>
        """

        # Resend API endpoint
        url = "https://api.resend.com/emails"
        
        # Email data
        data = {
            "from": "WeatherReport <onboarding@resend.dev>",
            "to": [recipient],
            "subject": "Your Weather Report",
            "html": html_content
        }

        # Send request to Resend API
        response = requests.post(
            url,
            json=data,
            headers={
                "Authorization": "re_VLNK2AwR_DGLq1kW5a6sTU1hscZEgKiRH",  # Replace with actual API key from resend.com
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            return True
        else:
            print(f"{COLORS['RED']}Error: {response.json().get('message', 'Unknown error')}{COLORS['END']}")
            return False

    except Exception as e:
        print(f"{COLORS['RED']}Error sending email: {str(e)}{COLORS['END']}")
        return False

def is_daytime(hour: int) -> bool:
    """Determine if it's daytime based on hour (6 AM to 6 PM)."""
    return 6 <= hour < 18

def get_ascii_art(weather_code: int, hour: int = None) -> str:
    """Return appropriate ASCII art based on weather code and time of day."""
    if hour is None:
        hour = datetime.now().hour

    is_day = is_daytime(hour)

    if weather_code == 0:  # Clear sky
        return WEATHER_ASCII['clear_day'] if is_day else WEATHER_ASCII['clear_night']
    elif weather_code in [1, 2, 3]:  # Cloudy conditions
        return WEATHER_ASCII['cloudy']
    elif weather_code in [51, 53, 61, 63, 80, 81]:  # Light/moderate rain
        return WEATHER_ASCII['rain_light']
    elif weather_code in [55, 65, 82]:  # Heavy rain
        return WEATHER_ASCII['rain_heavy']
    elif weather_code in [71, 73, 75, 77, 85, 86]:  # Snow
        return WEATHER_ASCII['snow']
    elif weather_code in [95, 96, 99]:  # Thunderstorm
        return WEATHER_ASCII['thunderstorm']
    elif weather_code in [45, 48]:  # Fog
        return WEATHER_ASCII['fog']
    return WEATHER_ASCII['clear_day'] if is_day else WEATHER_ASCII['clear_night']

def create_progress_bar(value: float, max_value: float, width: int = 20) -> str:
    """Create a visual progress bar."""
    percentage = min(value / max_value, 1.0)
    filled = int(width * percentage)
    return f"[{'█' * filled}{'░' * (width - filled)}]"

def format_hourly_forecast(hourly_data: Dict[str, Any], weather_codes: Dict[int, str], start_hour: int) -> str:
    """Format hourly forecast for the next 24 hours."""
    forecast = f"\n{COLORS['BOLD']}Hourly Forecast (Next 24 Hours):{COLORS['END']}\n"
    
    for i in range(24):
        hour_index = start_hour + i
        if hour_index >= len(hourly_data['time']):
            break
            
        # Get data for this hour
        temp = hourly_data['temperature_2m'][hour_index]
        precip_prob = hourly_data['precipitation_probability'][hour_index]
        weather_code = hourly_data['weather_code'][hour_index]
        
        # Format time
        time_str = datetime.fromisoformat(hourly_data['time'][hour_index]).strftime("%I %p")
        
        # Get weather symbol
        weather_symbol = "☀️" if weather_code == 0 else "⛅" if weather_code in [1, 2] else "☁️" if weather_code == 3 else \
                        "🌧️" if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82] else "🌨️" if weather_code in [71, 73, 75, 77, 85, 86] else \
                        "⛈️" if weather_code in [95, 96, 99] else "🌫️"
        
        # Temperature color
        temp_color = COLORS['BLUE'] if temp < 32 else COLORS['GREEN'] if temp < 65 else \
                    COLORS['YELLOW'] if temp < 85 else COLORS['RED']
        
        # Format hour line
        forecast += f"{COLORS['CYAN']}│{COLORS['END']} {time_str:>5} {weather_symbol} {temp_color}{temp:>4.1f}°F{COLORS['END']} "
        
        # Add precipitation probability if exists
        if precip_prob > 0:
            prob_bar = create_progress_bar(precip_prob, 100, 10)
            forecast += f" 💧 {prob_bar} {precip_prob}%"
        
        forecast += "\n"
        
        # Add separator every 6 hours
        if (i + 1) % 6 == 0 and i < 23:
            forecast += f"{COLORS['CYAN']}├{'─' * 50}┤{COLORS['END']}\n"
    
    return forecast

def get_weather_alert(hourly_data: Dict[str, Any], weather_codes: Dict[int, str], start_hour: int) -> str:
    """Generate weather alerts based on forecast data."""
    try:
        next_24_hours = list(zip(
            hourly_data['weather_code'][start_hour:start_hour+24],
            hourly_data['precipitation_probability'][start_hour:start_hour+24]
        ))
        
        alerts = []
        current_code = next_24_hours[0][0]
        max_precip_prob = max(prob for _, prob in next_24_hours)
        
        # Check precipitation probability
        if max_precip_prob >= 70:
            for hour, (code, prob) in enumerate(next_24_hours):
                if prob >= 70:
                    weather_type = "snow" if code in [71, 73, 75, 77, 85, 86] else "rain"
                    alerts.append(f"High chance of {weather_type} in {hour} hours ({prob}% probability)")
                    break
        elif max_precip_prob >= 40:
            for hour, (code, prob) in enumerate(next_24_hours):
                if prob >= 40:
                    weather_type = "snow" if code in [71, 73, 75, 77, 85, 86] else "rain"
                    alerts.append(f"Moderate chance of {weather_type} in {hour} hours ({prob}% probability)")
                    break
        
        # Check for weather changes
        for hour, (code, _) in enumerate(next_24_hours):
            if code != current_code:
                if current_code == 0 and code in [71, 73, 75, 77, 85, 86]:
                    alerts.append(f"Snow expected to start in {hour} hours")
                    break
                elif current_code == 0 and code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                    alerts.append(f"Rain expected to start in {hour} hours")
                    break
                elif code == 0 and current_code in [71, 73, 75, 77, 85, 86, 51, 53, 55, 61, 63, 65, 80, 81, 82]:
                    alerts.append(f"Precipitation expected to stop in {hour} hours")
                    break
                elif code == 0 and current_code in [1, 2, 3]:
                    alerts.append(f"Skies expected to clear in {hour} hours")
                    break
        
        if not alerts:
            current_condition = weather_codes.get(current_code, "Unknown")
            alerts.append(f"Weather expected to remain {current_condition.lower()} for the next 24 hours")
        
        return "\n".join(f"🔔 {alert}" for alert in alerts)
    except Exception as e:
        return f"Unable to generate weather alerts: {str(e)}"

def get_weather(zip_code: str) -> str:
    """Fetch and format weather data for the given ZIP code."""
    try:
        # Get coordinates from zip code
        geocode_url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=US&format=json"
        headers = {'User-Agent': 'WeatherApp/1.0'}
        location_response = requests.get(geocode_url, headers=headers)
        location_response.raise_for_status()
        location_data = location_response.json()

        if not location_data:
            return "Error: ZIP code not found"

        # Get coordinates
        lat = float(location_data[0]['lat'])
        lon = float(location_data[0]['lon'])
        location_name = location_data[0]['display_name'].split(',')[0]

        # Get weather data
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            f"&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max"
            f"&hourly=temperature_2m,precipitation_probability,weather_code"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
            f"&timezone=America/New_York"
            f"&forecast_days=5"
        )
        
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        # Weather code mapping
        weather_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
        }

        current = weather_data['current']
        daily = weather_data['daily']
        current_hour = datetime.now().hour

        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        # Generate output
        ascii_art = get_ascii_art(current['weather_code'])
        
        output = f"""
{COLORS['BOLD']}╔══════════════════════════════════════════════════════════════╗
║             Weather Report for {location_name} ({zip_code})             
╚══════════════════════════════════════════════════════════════╝{COLORS['END']}

{ascii_art}

{COLORS['BOLD']}Current Conditions:{COLORS['END']}
🌡️  Temperature: {current['temperature_2m']}°F
    {create_progress_bar(current['temperature_2m'], 100)}

💧 Humidity: {current['relative_humidity_2m']}%
    {create_progress_bar(current['relative_humidity_2m'], 100)}

🌪️  Wind Speed: {current['wind_speed_10m']} mph
    {create_progress_bar(current['wind_speed_10m'], 30)}

🌥️  Conditions: {weather_codes.get(current['weather_code'], 'Unknown')}

{COLORS['BOLD']}Weather Alerts:{COLORS['END']}
{get_weather_alert(weather_data['hourly'], weather_codes, current_hour)}

{format_hourly_forecast(weather_data['hourly'], weather_codes, current_hour)}

{COLORS['BOLD']}5-Day Forecast:{COLORS['END']}"""

        # Add forecast
        for i in range(5):
            date = datetime.fromisoformat(daily['time'][i]).strftime("%A, %B %d")
            output += f"""
{COLORS['CYAN']}┌──────────────────────────────────────┐
│ {date}
├──────────────────────────────────────┤
│ High: {daily['temperature_2m_max'][i]}°F  │  Low: {daily['temperature_2m_min'][i]}°F
│ {weather_codes.get(daily['weather_code'][i], 'Unknown')}
│ Precipitation Chance: {daily['precipitation_probability_max'][i]}%
└──────────────────────────────────────┘{COLORS['END']}"""

        return output

    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"

def main():
    """Main program loop."""
    try:
        # Display initial message
        print(f"{COLORS['BOLD']}Weather App with Email Support{COLORS['END']}")
        print("Note: Email feature requires a free API key from resend.com")
        
        while True:
            zip_code = input(f"{COLORS['BOLD']}Enter your ZIP code (or 'q' to quit): {COLORS['END']}")
            if zip_code.lower() == 'q':
                print("Thank you for using the Weather App!")
                break
                
            if not zip_code.isdigit() or len(zip_code) != 5:
                print(f"{COLORS['RED']}Please enter a valid 5-digit ZIP code.{COLORS['END']}")
                continue
            
            # Show loading animation
            print("Fetching weather data", end="")
            for _ in range(3):
                time.sleep(0.5)
                print(".", end="", flush=True)
            print("\n")
            
            weather_report = get_weather(zip_code)
            print(weather_report)
            
            # Ask if user wants to receive the report via email
            email_option = input(f"\n{COLORS['BOLD']}Would you like to receive this report via email? (y/n): {COLORS['END']}").lower()
            
            if email_option == 'y':
                email = input(f"{COLORS['BOLD']}Enter your email address: {COLORS['END']}")
                if is_valid_email(email):
                    print("Sending email...", end="")
                    if send_weather_email(email, weather_report):
                        print(f"\n{COLORS['GREEN']}Weather report sent successfully!{COLORS['END']}")
                    else:
                        print(f"\n{COLORS['RED']}Failed to send weather report.{COLORS['END']}")
                else:
                    print(f"{COLORS['RED']}Invalid email address.{COLORS['END']}")
            
            print("\nPress Enter to check another ZIP code or 'q' to quit...")
            if input().lower() == 'q':
                print("Thank you for using the Weather App!")
                break
                
    except KeyboardInterrupt:
        print("\nThank you for using the Weather App!")
    except Exception as e:
        print(f"{COLORS['RED']}An unexpected error occurred: {str(e)}{COLORS['END']}")

if __name__ == "__main__":
    main()