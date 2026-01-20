"""
Agent Executor - Bridges the Weather Agent with the A2A Protocol

This executor:
1. Receives A2A protocol messages
2. Parses user intent to determine weather query type
3. Routes to appropriate Weather agent skills
4. Returns formatted responses
"""
import re
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from weather_agent import WeatherAgent


class WeatherAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor for the Weather AI Agent.
    
    Routes incoming A2A messages to the appropriate Weather agent skills:
    - get_current: Current weather
    - get_forecast: Weather forecast
    - get_air_quality: Air quality index
    - get_recommendations: What to wear/do
    - compare: Compare two cities
    - summary: Complete weather summary
    - query: Natural language questions
    """
    
    def __init__(self):
        self.agent = WeatherAgent()
    
    def _extract_query(self, context: RequestContext) -> str:
        """Extract the user's text message from the A2A request."""
        
        # First check for our custom _user_text field (set by ServiceNow handler)
        if hasattr(context, '_user_text') and context._user_text:
            return context._user_text
        
        # Use the SDK's built-in method to get user input
        try:
            user_input = context.get_user_input()
            if user_input:
                return user_input
        except Exception:
            pass
        
        # Fallback: try to extract from message directly
        try:
            if context.message and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, 'text') and part.text:
                        return part.text
        except Exception:
            pass
        
        # Another fallback: check _message attribute
        try:
            if hasattr(context, '_message') and context._message:
                for part in context._message.parts:
                    if hasattr(part, 'text') and part.text:
                        return part.text
        except Exception:
            pass
        
        # Another fallback: check request params
        try:
            if context.request and context.request.message:
                msg = context.request.message
                if hasattr(msg, 'parts') and msg.parts:
                    for part in msg.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
        except Exception:
            pass
        
        return ""
    
    def _extract_city(self, query: str) -> str | None:
        """Extract city name from query."""
        # Common patterns for city extraction
        patterns = [
            r"(?:in|for|at)\s+([A-Za-z\s]+?)(?:\s*,\s*([A-Z]{2}))?\s*(?:\?|$|today|tomorrow|this|next)",
            r"(?:weather|forecast|temperature|air quality)\s+(?:in|for|at)?\s*([A-Za-z\s]+?)(?:\s*,\s*([A-Z]{2}))?\s*(?:\?|$)",
            r"([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+weather",
            r"([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+forecast",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                country = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                if country:
                    return f"{city},{country}"
                return city
        
        # Try to find capitalized words that might be city names
        # Skip common weather words
        skip_words = {'weather', 'forecast', 'temperature', 'humidity', 'wind', 'rain', 
                      'snow', 'sunny', 'cloudy', 'air', 'quality', 'today', 'tomorrow',
                      'what', 'how', 'is', 'the', 'in', 'for', 'at', 'get', 'show', 'tell',
                      'me', 'current', 'now', 'compare', 'vs', 'and', 'between'}
        
        words = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', query)
        for word in words:
            if word.lower() not in skip_words:
                return word
        
        return None
    
    def _parse_intent(self, query: str) -> tuple[str, dict]:
        """
        Parse user query to determine which skill to invoke.
        
        Returns:
            tuple: (skill_name, parameters)
        """
        query_lower = query.lower().strip()
        
        # =====================================================================
        # Intent: Compare Weather (two cities)
        # Examples: "compare London and Paris", "weather London vs Tokyo"
        # =====================================================================
        compare_patterns = [
            r"compare\s+([A-Za-z\s]+?)\s+(?:and|vs|versus|with)\s+([A-Za-z\s]+)",
            r"([A-Za-z\s]+?)\s+(?:vs|versus)\s+([A-Za-z\s]+)",
            r"weather\s+(?:in\s+)?([A-Za-z\s]+?)\s+(?:and|vs|or)\s+([A-Za-z\s]+)",
        ]
        
        for pattern in compare_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                city1 = match.group(1).strip()
                city2 = match.group(2).strip()
                return ("compare", {"city1": city1, "city2": city2})
        
        # =====================================================================
        # Intent: Weather Forecast
        # Examples: "forecast for London", "5 day forecast Tokyo"
        # =====================================================================
        if any(word in query_lower for word in ["forecast", "next few days", "this week", "tomorrow"]):
            city = self._extract_city(query)
            
            # Extract number of days
            days_match = re.search(r"(\d+)\s*day", query_lower)
            days = int(days_match.group(1)) if days_match else 3
            
            if city:
                return ("forecast", {"city": city, "days": days})
        
        # =====================================================================
        # Intent: Air Quality
        # Examples: "air quality in Delhi", "pollution in Beijing"
        # =====================================================================
        if any(word in query_lower for word in ["air quality", "aqi", "pollution", "smog"]):
            city = self._extract_city(query)
            if city:
                return ("air_quality", {"city": city})
        
        # =====================================================================
        # Intent: Recommendations
        # Examples: "what to wear in London", "should I take umbrella"
        # =====================================================================
        if any(phrase in query_lower for phrase in ["what to wear", "should i", "recommend", "suggestion", "umbrella", "jacket"]):
            city = self._extract_city(query)
            if city:
                return ("recommendations", {"city": city})
        
        # =====================================================================
        # Intent: Complete Summary
        # Examples: "complete weather summary for Paris", "full report London"
        # =====================================================================
        if any(phrase in query_lower for phrase in ["summary", "complete", "full report", "everything", "all info"]):
            city = self._extract_city(query)
            if city:
                return ("summary", {"city": city})
        
        # =====================================================================
        # Intent: Current Weather (default for city queries)
        # Examples: "weather in London", "temperature in Tokyo", "London weather"
        # =====================================================================
        if any(word in query_lower for word in ["weather", "temperature", "temp", "hot", "cold", "rain", "sunny", "cloudy", "humid"]):
            city = self._extract_city(query)
            if city:
                return ("current", {"city": city})
        
        # Check if query is just a city name
        city = self._extract_city(query)
        if city and len(query.split()) <= 3:
            return ("current", {"city": city})
        
        # =====================================================================
        # Default: Natural Language Query
        # =====================================================================
        return ("query", {"question": query})
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Handle incoming A2A requests.
        """
        query = self._extract_query(context)
        
        # Debug logging
        print(f"[DEBUG] Extracted query: '{query}'")
        
        # Handle empty queries
        if not query or query.strip() == "":
            response = self._get_help_message()
            await event_queue.enqueue_event(new_agent_text_message(response))
            return
        
        # Parse intent and get parameters
        skill, params = self._parse_intent(query)
        
        print(f"[DEBUG] Parsed intent: {skill}, params: {params}")
        
        # Route to appropriate skill
        try:
            if skill == "current":
                response = await self.agent.get_current_weather(
                    city=params["city"]
                )
            
            elif skill == "forecast":
                response = await self.agent.get_forecast(
                    city=params["city"],
                    days=params.get("days", 3)
                )
            
            elif skill == "air_quality":
                response = await self.agent.get_air_quality(
                    city=params["city"]
                )
            
            elif skill == "recommendations":
                response = await self.agent.get_recommendations(
                    city=params["city"]
                )
            
            elif skill == "compare":
                response = await self.agent.compare_weather(
                    city1=params["city1"],
                    city2=params["city2"]
                )
            
            elif skill == "summary":
                response = await self.agent.get_weather_summary(
                    city=params["city"]
                )
            
            else:  # query (natural language)
                response = await self.agent.query(
                    question=params.get("question", query)
                )
        
        except Exception as e:
            response = f"❌ Error: {str(e)}"
        
        # Send response
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Handle cancellation requests."""
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancelled.")
        )
    
    def _get_help_message(self) -> str:
        """Return help message explaining available capabilities."""
        return """# ☀️ Weather AI Agent

I'm your AI-powered weather assistant! Here's what I can do:

## 📋 Available Commands

### 🌡️ Current Weather
Get current conditions for any city:
- "Weather in London"
- "Temperature in Tokyo"
- "New York weather"

### 📅 Weather Forecast
Get up to 5-day forecast:
- "Forecast for Paris"
- "5 day forecast London"
- "What's the weather tomorrow in Berlin"

### 💨 Air Quality
Check air quality index:
- "Air quality in Delhi"
- "AQI Beijing"
- "Pollution in Los Angeles"

### 👕 Recommendations
Get clothing and activity suggestions:
- "What to wear in London"
- "Should I take an umbrella in Seattle"

### 🌍 Compare Cities
Compare weather between two cities:
- "Compare London and Paris"
- "Tokyo vs New York weather"

### 📊 Complete Summary
Get full weather report:
- "Weather summary for Sydney"
- "Complete weather report Tokyo"

### 💬 Natural Language
Ask anything about weather:
- "Is it a good day for hiking in Denver?"
- "Will it rain this weekend in Miami?"

---
**Tip:** Just type a city name for quick current weather!
"""
