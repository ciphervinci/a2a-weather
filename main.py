"""
A2A Weather Agent Server - Main Entry Point
"""
import os
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import WeatherAgentExecutor
from weather_agent import WeatherAgent

load_dotenv()


def get_agent_card(host: str, port: int) -> AgentCard:
    """Create the Agent Card for the Weather Agent."""
    
    # Skill 1: Current Weather
    current_weather_skill = AgentSkill(
        id="current_weather",
        name="Current Weather",
        description="Get current weather conditions for any city including temperature, humidity, wind, and more.",
        tags=["weather", "current", "temperature", "conditions"],
        examples=[
            "Weather in London",
            "Current temperature in Tokyo",
            "What's the weather in New York?",
        ],
    )
    
    # Skill 2: Weather Forecast
    forecast_skill = AgentSkill(
        id="forecast",
        name="Weather Forecast",
        description="Get weather forecast for up to 5 days with daily high/low temperatures.",
        tags=["weather", "forecast", "prediction", "future"],
        examples=[
            "5 day forecast for Paris",
            "Weather forecast London",
            "What's the weather tomorrow in Berlin?",
        ],
    )
    
    # Skill 3: Air Quality
    air_quality_skill = AgentSkill(
        id="air_quality",
        name="Air Quality Index",
        description="Get air quality index and pollution levels for any city.",
        tags=["air", "quality", "pollution", "aqi", "health"],
        examples=[
            "Air quality in Delhi",
            "AQI for Beijing",
            "Pollution levels in Los Angeles",
        ],
    )
    
    # Skill 4: Recommendations
    recommendations_skill = AgentSkill(
        id="recommendations",
        name="Weather Recommendations",
        description="Get AI-powered recommendations for clothing and activities based on weather.",
        tags=["recommendations", "clothing", "activities", "advice"],
        examples=[
            "What to wear in London today",
            "Should I take an umbrella in Seattle?",
            "Good day for outdoor activities in Miami?",
        ],
    )
    
    # Skill 5: Compare Cities
    compare_skill = AgentSkill(
        id="compare",
        name="Compare Weather",
        description="Compare weather conditions between two cities side by side.",
        tags=["compare", "comparison", "cities", "versus"],
        examples=[
            "Compare weather London and Paris",
            "Tokyo vs New York weather",
            "Weather difference between Miami and Seattle",
        ],
    )
    
    # Skill 6: Weather Summary
    summary_skill = AgentSkill(
        id="summary",
        name="Complete Weather Summary",
        description="Get comprehensive weather report including current conditions, forecast, and air quality.",
        tags=["summary", "complete", "report", "comprehensive"],
        examples=[
            "Complete weather summary for Sydney",
            "Full weather report Tokyo",
            "All weather info for London",
        ],
    )
    
    # Skill 7: Natural Language Query
    query_skill = AgentSkill(
        id="query",
        name="Natural Language Query",
        description="Ask any weather-related question in natural language.",
        tags=["question", "natural-language", "ai", "ask"],
        examples=[
            "Is it a good day for hiking in Denver?",
            "Will it rain this weekend in Chicago?",
            "Should I plan a beach trip to LA tomorrow?",
        ],
    )
    
    # Agent capabilities
    capabilities = AgentCapabilities(
        streaming=False,
        pushNotifications=False,
    )
    
    # Determine URL
    host_url = os.getenv("HOST_URL")
    if host_url:
        url = host_url.rstrip("/") + "/"
    else:
        url = f"http://{host}:{port}/"
    
    # Create Agent Card
    agent_card = AgentCard(
        name="Weather AI Agent",
        description="AI-powered weather assistant providing current conditions, forecasts, "
                    "air quality, recommendations, and city comparisons. "
                    "Powered by OpenWeatherMap and Gemini AI.",
        url=url,
        version="1.0.0",
        defaultInputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[
            current_weather_skill,
            forecast_skill,
            air_quality_skill,
            recommendations_skill,
            compare_skill,
            summary_skill,
            query_skill,
        ],
    )
    
    return agent_card


def create_app(host: str = "0.0.0.0", port: int = 8002):
    """Create and configure the A2A Starlette application."""
    
    agent_executor = WeatherAgentExecutor()
    
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    app = A2AStarletteApplication(
        agent_card=get_agent_card(host, port),
        http_handler=request_handler,
    )
    
    return app.build()


def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        ("OPENWEATHER_API_KEY", "OpenWeatherMap API key (free at openweathermap.org)"),
        ("GEMINI_API_KEY", "Google Gemini API key"),
    ]
    
    missing = []
    for var, description in required_vars:
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")
    
    if missing:
        print("❌ Missing required environment variables:")
        print("\n".join(missing))
        print("\nSee .env.example for configuration details.")
        return False
    
    return True


def main():
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A2A Weather Agent Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("PORT", 8000)),
        help="Port to listen on"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not validate_environment():
        exit(1)
    
    # Print startup info
    print("=" * 60)
    print("☀️  Weather A2A Agent")
    print("=" * 60)
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"📋 Agent Card: http://{args.host}:{args.port}/.well-known/agent.json")
    print("=" * 60)
    print("\n🚀 Starting server...\n")
    
    # Create and run app
    app = create_app(args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
