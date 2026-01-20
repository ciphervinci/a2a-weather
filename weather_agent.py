"""
Weather AI Agent - Combines weather data with AI-powered insights

This agent provides:
1. Current weather conditions
2. Weather forecasts (up to 5 days)
3. Air quality information
4. Weather-based recommendations
5. Natural language weather queries
"""
import os
import json
from typing import Any
from google import genai

from weather_client import WeatherClient


class WeatherAgent:
    """
    AI-powered Weather Agent.
    
    This agent:
    - Fetches weather data from OpenWeatherMap
    - Uses Gemini AI for natural language understanding
    - Provides weather-based recommendations
    """
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        """Initialize Weather client and Gemini AI."""
        self.weather = WeatherClient()
        
        # Initialize Gemini for AI features
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.genai_client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
    
    async def _ai_analyze(self, prompt: str) -> str:
        """Use Gemini to analyze and generate insights."""
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"
    
    # =========================================================================
    # SKILL 1: Get Current Weather
    # =========================================================================
    
    async def get_current_weather(self, city: str) -> str:
        """
        Get current weather for a city.
        
        Args:
            city: City name (e.g., 'London', 'New York', 'Tokyo')
            
        Returns:
            Formatted current weather information
        """
        try:
            data = await self.weather.get_current_weather(city=city)
            return self.weather.format_current_weather(data)
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                return f"❌ City '{city}' not found. Please check the spelling or try adding a country code (e.g., 'Paris,FR')."
            return f"❌ Error fetching weather for {city}: {error_msg}"
    
    # =========================================================================
    # SKILL 2: Get Weather Forecast
    # =========================================================================
    
    async def get_forecast(self, city: str, days: int = 3) -> str:
        """
        Get weather forecast for a city.
        
        Args:
            city: City name
            days: Number of days (1-5)
            
        Returns:
            Formatted forecast information
        """
        try:
            days = min(max(days, 1), 5)  # Clamp between 1 and 5
            data = await self.weather.get_forecast(city=city)
            return self.weather.format_forecast(data, days=days)
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                return f"❌ City '{city}' not found."
            return f"❌ Error fetching forecast for {city}: {error_msg}"
    
    # =========================================================================
    # SKILL 3: Get Air Quality
    # =========================================================================
    
    async def get_air_quality(self, city: str) -> str:
        """
        Get air quality index for a city.
        
        Args:
            city: City name
            
        Returns:
            Formatted air quality information
        """
        try:
            # First, geocode the city to get coordinates
            locations = await self.weather.geocode(city)
            
            if not locations:
                return f"❌ City '{city}' not found."
            
            lat = locations[0].get("lat")
            lon = locations[0].get("lon")
            city_name = locations[0].get("name", city)
            country = locations[0].get("country", "")
            
            # Get air quality data
            data = await self.weather.get_air_quality(lat, lon)
            
            result = self.weather.format_air_quality(data)
            return f"📍 **{city_name}, {country}**\n\n{result}"
            
        except Exception as e:
            return f"❌ Error fetching air quality for {city}: {str(e)}"
    
    # =========================================================================
    # SKILL 4: Get Weather Recommendations
    # =========================================================================
    
    async def get_recommendations(self, city: str) -> str:
        """
        Get AI-powered weather recommendations.
        
        Args:
            city: City name
            
        Returns:
            Weather-based activity and clothing recommendations
        """
        try:
            # Get current weather
            weather_data = await self.weather.get_current_weather(city=city)
            
            # Get AI recommendations
            ai_prompt = f"""Based on this weather data, provide brief, practical recommendations:

Weather Data:
{json.dumps(weather_data, indent=2)}

Provide:
1. **What to Wear** (2-3 items)
2. **Activities** (2-3 suggestions appropriate for this weather)
3. **Health Tips** (1-2 tips based on conditions)

Keep it concise and friendly!"""

            recommendations = await self._ai_analyze(ai_prompt)
            
            # Format output
            formatted_weather = self.weather.format_current_weather(weather_data)
            
            return f"{formatted_weather}\n\n---\n\n## 🎯 Recommendations\n\n{recommendations}"
            
        except Exception as e:
            return f"❌ Error getting recommendations for {city}: {str(e)}"
    
    # =========================================================================
    # SKILL 5: Compare Weather
    # =========================================================================
    
    async def compare_weather(self, city1: str, city2: str) -> str:
        """
        Compare weather between two cities.
        
        Args:
            city1: First city
            city2: Second city
            
        Returns:
            Side-by-side weather comparison
        """
        try:
            # Fetch weather for both cities
            data1 = await self.weather.get_current_weather(city=city1)
            data2 = await self.weather.get_current_weather(city=city2)
            
            # Extract key metrics
            def extract_metrics(data):
                return {
                    "city": f"{data.get('name', 'Unknown')}, {data.get('sys', {}).get('country', '')}",
                    "temp": data.get("main", {}).get("temp", 0),
                    "feels_like": data.get("main", {}).get("feels_like", 0),
                    "humidity": data.get("main", {}).get("humidity", 0),
                    "wind": data.get("wind", {}).get("speed", 0),
                    "description": data.get("weather", [{}])[0].get("description", "Unknown").capitalize(),
                    "icon": self.weather._get_weather_emoji(data.get("weather", [{}])[0].get("icon", "")),
                }
            
            m1 = extract_metrics(data1)
            m2 = extract_metrics(data2)
            
            # Build comparison
            output = [
                "# 🌍 Weather Comparison",
                "",
                f"| Metric | {m1['city']} | {m2['city']} |",
                "|--------|------------|------------|",
                f"| Condition | {m1['icon']} {m1['description']} | {m2['icon']} {m2['description']} |",
                f"| Temperature | {m1['temp']:.1f}°C | {m2['temp']:.1f}°C |",
                f"| Feels Like | {m1['feels_like']:.1f}°C | {m2['feels_like']:.1f}°C |",
                f"| Humidity | {m1['humidity']}% | {m2['humidity']}% |",
                f"| Wind | {m1['wind']} m/s | {m2['wind']} m/s |",
            ]
            
            # Add AI summary
            temp_diff = abs(m1['temp'] - m2['temp'])
            warmer = m1['city'] if m1['temp'] > m2['temp'] else m2['city']
            
            output.append("")
            output.append(f"**Summary:** {warmer} is warmer by {temp_diff:.1f}°C")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error comparing weather: {str(e)}"
    
    # =========================================================================
    # SKILL 6: Natural Language Query
    # =========================================================================
    
    async def query(self, question: str) -> str:
        """
        Answer natural language questions about weather.
        
        Args:
            question: Natural language question
            
        Returns:
            AI-generated answer
        """
        try:
            # Try to extract city from question
            ai_prompt = f"""Extract the city name from this weather question. 
If no specific city is mentioned, respond with "NONE".
Only respond with the city name or "NONE", nothing else.

Question: {question}"""
            
            city_response = await self._ai_analyze(ai_prompt)
            city = city_response.strip() if city_response.strip().upper() != "NONE" else None
            
            if city:
                # Get weather data for context
                try:
                    weather_data = await self.weather.get_current_weather(city=city)
                    weather_context = json.dumps(weather_data, indent=2)
                except:
                    weather_context = "Weather data unavailable"
            else:
                weather_context = "No specific city mentioned"
            
            # Generate response
            ai_prompt = f"""You are a friendly weather assistant. Answer this question:

Question: {question}

Weather Data (if available):
{weather_context}

Provide a helpful, conversational answer. If no city was specified and the question needs one, 
ask the user which city they're interested in."""

            response = await self._ai_analyze(ai_prompt)
            return response
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
    
    # =========================================================================
    # SKILL 7: Weather Alerts Summary
    # =========================================================================
    
    async def get_weather_summary(self, city: str) -> str:
        """
        Get a comprehensive weather summary with alerts.
        
        Args:
            city: City name
            
        Returns:
            Complete weather summary with current, forecast, and air quality
        """
        try:
            # Gather all data
            current = await self.weather.get_current_weather(city=city)
            forecast = await self.weather.get_forecast(city=city)
            
            # Get coordinates for air quality
            locations = await self.weather.geocode(city)
            air_quality = None
            if locations:
                lat = locations[0].get("lat")
                lon = locations[0].get("lon")
                air_quality = await self.weather.get_air_quality(lat, lon)
            
            # Format each section
            current_formatted = self.weather.format_current_weather(current)
            forecast_formatted = self.weather.format_forecast(forecast, days=3)
            
            output = [
                f"# 📊 Complete Weather Summary",
                "",
                "## Current Conditions",
                current_formatted,
                "",
                "---",
                "",
                forecast_formatted,
            ]
            
            if air_quality:
                output.append("")
                output.append("---")
                output.append("")
                output.append("## Air Quality")
                output.append(self.weather.format_air_quality(air_quality))
            
            # Add AI-generated insights
            ai_prompt = f"""Based on this weather data, provide a brief (2-3 sentence) overall assessment:
            
Current: {json.dumps(current.get('main', {}), indent=2)}
Conditions: {current.get('weather', [{}])[0].get('description', 'Unknown')}

Is it a good day to be outside? Any weather concerns?"""

            insights = await self._ai_analyze(ai_prompt)
            
            output.append("")
            output.append("---")
            output.append("")
            output.append("## 🤖 AI Insights")
            output.append(insights)
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error getting weather summary for {city}: {str(e)}"
