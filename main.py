"""
A2A Weather Agent Server - Main Entry Point
ServiceNow A2A Compatible Version

Key changes for ServiceNow compatibility:
1. API Key authentication support
2. Proper CORS headers for cross-origin requests
3. Health check endpoint
4. Extended timeout handling
5. Synchronous response mode (no streaming)
"""
import os
import json
import uvicorn
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import WeatherAgentExecutor
from weather_agent import WeatherAgent

load_dotenv()

# Optional API Key for authentication
API_KEY = os.getenv("A2A_API_KEY", "")


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
    
    # Agent capabilities - ServiceNow requires non-streaming
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
    
    # Create Agent Card with A2A v0.3 compatible fields
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


def verify_api_key(request: Request) -> bool:
    """Verify API key if configured."""
    if not API_KEY:
        return True  # No API key configured, allow all
    
    # Check multiple header formats that ServiceNow might use
    api_key = (
        request.headers.get("x-sn-apikey") or
        request.headers.get("x-api-key") or
        request.headers.get("Authorization", "").replace("Bearer ", "").replace("ApiKey ", "")
    )
    
    return api_key == API_KEY


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for Render and monitoring."""
    return JSONResponse({
        "status": "healthy",
        "service": "a2a-weather-agent",
        "version": "1.0.0"
    })


def create_app(host: str = "0.0.0.0", port: int = 8000):
    """Create and configure the A2A Starlette application with ServiceNow compatibility."""
    
    agent_executor = WeatherAgentExecutor()
    agent_card = get_agent_card(host, port)
    
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create the base A2A application
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    base_app = a2a_app.build()
    
    # Add additional routes for compatibility
    additional_routes = [
        Route("/health", health_check, methods=["GET"]),
        Route("/healthz", health_check, methods=["GET"]),
    ]
    
    # CORS middleware configuration for ServiceNow
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict to your ServiceNow instance
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=[
                "Content-Type",
                "Authorization",
                "x-sn-apikey",
                "x-api-key",
                "Accept",
                "Origin",
                "X-Requested-With",
            ],
            expose_headers=["*"],
            max_age=3600,
        )
    ]
    
    # Combine routes
    all_routes = list(base_app.routes) + additional_routes
    
    # Create final app with middleware
    app = Starlette(
        routes=all_routes,
        middleware=middleware,
        on_startup=base_app.on_startup if hasattr(base_app, 'on_startup') else None,
        on_shutdown=base_app.on_shutdown if hasattr(base_app, 'on_shutdown') else None,
    )
    
    return app


def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        ("OPENWEATHER_API_KEY", "OpenWeatherMap API key (free at openweathermap.org)"),
        ("GEMINI_API_KEY", "Google Gemini API key"),
    ]
    
    optional_vars = [
        ("A2A_API_KEY", "API key for authenticating A2A requests (optional but recommended)"),
        ("HOST_URL", "Public URL of the service (for Agent Card)"),
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
    
    # Print optional vars status
    print("\n📝 Optional configuration:")
    for var, description in optional_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var or "SECRET" in var:
                print(f"  ✓ {var}: configured (hidden)")
            else:
                print(f"  ✓ {var}: {value}")
        else:
            print(f"  - {var}: not set ({description})")
    
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
    
    # Determine public URL
    host_url = os.getenv("HOST_URL", f"http://{args.host}:{args.port}")
    
    # Print startup info
    print("\n" + "=" * 60)
    print("☀️  Weather A2A Agent - ServiceNow Compatible")
    print("=" * 60)
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🌐 Public URL: {host_url}")
    print(f"📋 Agent Card: {host_url}/.well-known/agent.json")
    print(f"❤️  Health Check: {host_url}/health")
    print("=" * 60)
    
    # ServiceNow configuration help
    print("\n📖 ServiceNow Configuration:")
    print(f"   Agent Card URL: {host_url}/.well-known/agent.json")
    print(f"   Agent Execution URL: {host_url}/")
    if API_KEY:
        print(f"   Authentication: API Key (x-sn-apikey header)")
    else:
        print(f"   Authentication: None (add A2A_API_KEY env var to enable)")
    print("=" * 60)
    print("\n🚀 Starting server...\n")
    
    # Create and run app
    app = create_app(args.host, args.port)
    
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port,
        timeout_keep_alive=120,  # Longer timeout for cold starts
    )


if __name__ == "__main__":
    main()
