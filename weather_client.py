"""
Weather API Client - Fetches weather data from OpenWeatherMap API

Free API: https://openweathermap.org/api
- Current weather
- 5-day forecast
- Air quality
"""
import os
from datetime import datetime
from typing import Any
import httpx


class WeatherClient:
    """
    Client for OpenWeatherMap API.
    
    Free tier includes:
    - Current weather data
    - 5-day / 3-hour forecast
    - Basic geocoding
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "https://api.openweathermap.org/geo/1.0"
    
    def __init__(self):
        """Initialize the Weather client with API key."""
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable is required")
    
    async def _make_request(self, url: str, params: dict) -> dict[str, Any]:
        """Make an async HTTP request to the Weather API."""
        params["appid"] = self.api_key
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # GEOCODING - Convert city names to coordinates
    # =========================================================================
    
    async def geocode(self, city: str, country_code: str = None, limit: int = 5) -> list[dict]:
        """
        Convert city name to coordinates.
        
        Args:
            city: City name
            country_code: Optional ISO 3166 country code (e.g., 'US', 'GB', 'IN')
            limit: Max results
            
        Returns:
            List of matching locations with lat/lon
        """
        query = f"{city},{country_code}" if country_code else city
        
        params = {
            "q": query,
            "limit": limit,
        }
        
        url = f"{self.GEO_URL}/direct"
        return await self._make_request(url, params)
    
    # =========================================================================
    # CURRENT WEATHER
    # =========================================================================
    
    async def get_current_weather(
        self,
        city: str = None,
        lat: float = None,
        lon: float = None,
        units: str = "metric"
    ) -> dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            city: City name (e.g., 'London', 'New York,US')
            lat: Latitude (alternative to city)
            lon: Longitude (alternative to city)
            units: 'metric' (Celsius), 'imperial' (Fahrenheit), 'standard' (Kelvin)
            
        Returns:
            Current weather data
        """
        params = {"units": units}
        
        if city:
            params["q"] = city
        elif lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        else:
            raise ValueError("Either city or lat/lon must be provided")
        
        url = f"{self.BASE_URL}/weather"
        return await self._make_request(url, params)
    
    # =========================================================================
    # WEATHER FORECAST
    # =========================================================================
    
    async def get_forecast(
        self,
        city: str = None,
        lat: float = None,
        lon: float = None,
        units: str = "metric"
    ) -> dict[str, Any]:
        """
        Get 5-day / 3-hour weather forecast.
        
        Args:
            city: City name
            lat: Latitude
            lon: Longitude
            units: Temperature units
            
        Returns:
            5-day forecast data (40 data points, every 3 hours)
        """
        params = {"units": units}
        
        if city:
            params["q"] = city
        elif lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        else:
            raise ValueError("Either city or lat/lon must be provided")
        
        url = f"{self.BASE_URL}/forecast"
        return await self._make_request(url, params)
    
    # =========================================================================
    # AIR QUALITY (requires One Call API subscription for full features)
    # =========================================================================
    
    async def get_air_quality(
        self,
        lat: float,
        lon: float
    ) -> dict[str, Any]:
        """
        Get air quality index for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Air quality data with AQI and pollutant levels
        """
        params = {
            "lat": lat,
            "lon": lon,
        }
        
        url = f"{self.BASE_URL}/air_pollution"
        return await self._make_request(url, params)
    
    # =========================================================================
    # FORMATTED RESPONSES
    # =========================================================================
    
    def format_current_weather(self, data: dict) -> str:
        """Format current weather data into a readable string."""
        try:
            city = data.get("name", "Unknown")
            country = data.get("sys", {}).get("country", "")
            
            weather = data.get("weather", [{}])[0]
            description = weather.get("description", "Unknown").capitalize()
            icon = self._get_weather_emoji(weather.get("icon", ""))
            
            main = data.get("main", {})
            temp = main.get("temp", 0)
            feels_like = main.get("feels_like", 0)
            humidity = main.get("humidity", 0)
            pressure = main.get("pressure", 0)
            
            wind = data.get("wind", {})
            wind_speed = wind.get("speed", 0)
            
            clouds = data.get("clouds", {}).get("all", 0)
            
            visibility = data.get("visibility", 0) / 1000  # Convert to km
            
            # Sunrise/Sunset
            sys_data = data.get("sys", {})
            sunrise = datetime.fromtimestamp(sys_data.get("sunrise", 0)).strftime("%H:%M")
            sunset = datetime.fromtimestamp(sys_data.get("sunset", 0)).strftime("%H:%M")
            
            return f"""
{icon} **Current Weather in {city}, {country}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Condition:** {description}
**Temperature:** {temp:.1f}°C (Feels like {feels_like:.1f}°C)
**Humidity:** {humidity}%
**Wind:** {wind_speed} m/s
**Pressure:** {pressure} hPa
**Cloud Cover:** {clouds}%
**Visibility:** {visibility:.1f} km

🌅 Sunrise: {sunrise} | 🌇 Sunset: {sunset}
""".strip()
        except Exception as e:
            return f"Error formatting weather: {str(e)}"
    
    def format_forecast(self, data: dict, days: int = 3) -> str:
        """Format forecast data into a readable string."""
        try:
            city = data.get("city", {}).get("name", "Unknown")
            country = data.get("city", {}).get("country", "")
            
            forecasts = data.get("list", [])
            
            output = [f"📅 **{days}-Day Forecast for {city}, {country}**"]
            output.append("━" * 40)
            
            # Group by day
            daily_forecasts = {}
            for forecast in forecasts:
                dt = datetime.fromtimestamp(forecast.get("dt", 0))
                date_key = dt.strftime("%Y-%m-%d")
                
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = []
                daily_forecasts[date_key].append(forecast)
            
            # Show only requested number of days
            for i, (date, day_forecasts) in enumerate(list(daily_forecasts.items())[:days]):
                dt = datetime.strptime(date, "%Y-%m-%d")
                day_name = dt.strftime("%A, %b %d")
                
                # Get min/max temps for the day
                temps = [f.get("main", {}).get("temp", 0) for f in day_forecasts]
                min_temp = min(temps) if temps else 0
                max_temp = max(temps) if temps else 0
                
                # Get most common weather condition
                conditions = [f.get("weather", [{}])[0] for f in day_forecasts]
                main_condition = conditions[len(conditions)//2] if conditions else {}
                description = main_condition.get("description", "Unknown").capitalize()
                icon = self._get_weather_emoji(main_condition.get("icon", ""))
                
                output.append(f"\n**{day_name}** {icon}")
                output.append(f"  {description}")
                output.append(f"  🌡️ {min_temp:.0f}°C - {max_temp:.0f}°C")
            
            return "\n".join(output)
        except Exception as e:
            return f"Error formatting forecast: {str(e)}"
    
    def format_air_quality(self, data: dict) -> str:
        """Format air quality data into a readable string."""
        try:
            aqi_list = data.get("list", [{}])
            if not aqi_list:
                return "No air quality data available."
            
            aqi_data = aqi_list[0]
            main = aqi_data.get("main", {})
            aqi = main.get("aqi", 0)
            
            components = aqi_data.get("components", {})
            
            # AQI scale: 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
            aqi_labels = {
                1: ("Good", "🟢"),
                2: ("Fair", "🟡"),
                3: ("Moderate", "🟠"),
                4: ("Poor", "🔴"),
                5: ("Very Poor", "🟣"),
            }
            
            label, emoji = aqi_labels.get(aqi, ("Unknown", "⚪"))
            
            return f"""
{emoji} **Air Quality Index: {aqi} ({label})**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pollutant Levels:**
• CO: {components.get('co', 0):.1f} μg/m³
• NO₂: {components.get('no2', 0):.1f} μg/m³
• O₃: {components.get('o3', 0):.1f} μg/m³
• PM2.5: {components.get('pm2_5', 0):.1f} μg/m³
• PM10: {components.get('pm10', 0):.1f} μg/m³
• SO₂: {components.get('so2', 0):.1f} μg/m³
""".strip()
        except Exception as e:
            return f"Error formatting air quality: {str(e)}"
    
    def _get_weather_emoji(self, icon_code: str) -> str:
        """Convert OpenWeatherMap icon code to emoji."""
        icon_map = {
            "01d": "☀️",  # Clear sky day
            "01n": "🌙",  # Clear sky night
            "02d": "⛅",  # Few clouds day
            "02n": "☁️",  # Few clouds night
            "03d": "☁️",  # Scattered clouds
            "03n": "☁️",
            "04d": "☁️",  # Broken clouds
            "04n": "☁️",
            "09d": "🌧️",  # Shower rain
            "09n": "🌧️",
            "10d": "🌦️",  # Rain day
            "10n": "🌧️",  # Rain night
            "11d": "⛈️",  # Thunderstorm
            "11n": "⛈️",
            "13d": "❄️",  # Snow
            "13n": "❄️",
            "50d": "🌫️",  # Mist
            "50n": "🌫️",
        }
        return icon_map.get(icon_code, "🌤️")
