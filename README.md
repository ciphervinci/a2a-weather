# ☀️ A2A Weather AI Agent

An [A2A Protocol](https://a2a-protocol.org/) compliant agent that provides weather information, forecasts, air quality data, and AI-powered recommendations.

## 🎯 Features (A2A Skills)

| Skill | Description | Example |
|-------|-------------|---------|
| **Current Weather** | Real-time weather conditions | `"Weather in London"` |
| **Weather Forecast** | Up to 5-day forecast | `"5 day forecast Tokyo"` |
| **Air Quality** | AQI and pollution levels | `"Air quality in Delhi"` |
| **Recommendations** | What to wear/do based on weather | `"What to wear in Paris"` |
| **Compare Cities** | Side-by-side comparison | `"Compare London vs Paris"` |
| **Weather Summary** | Complete weather report | `"Weather summary Sydney"` |
| **Natural Language** | Ask anything about weather | `"Good day for hiking?"` |

## 🚀 Quick Start

### 1. Get API Keys (Both Free!)

**OpenWeatherMap API Key:**
1. Sign up at [openweathermap.org](https://home.openweathermap.org/users/sign_up)
2. Go to API Keys section
3. Generate a new key (free tier: 60 calls/minute)

**Google Gemini API Key:**
1. Go to [aistudio.google.com](https://aistudio.google.com/app/apikey)
2. Create a new API key

### 2. Clone & Setup

```bash
git clone <your-repo-url>
cd a2a-weather-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

```bash
OPENWEATHER_API_KEY=your_openweather_key
GEMINI_API_KEY=your_gemini_key
```

### 4. Run the Server

```bash
python main.py
```

### 5. Test

```bash
# In another terminal
python test_client.py

# Or use curl
curl http://localhost:8000/.well-known/agent.json
```

## 🔌 API Examples

### Get Current Weather

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Weather in London"}],
        "messageId": "msg-1"
      }
    }
  }'
```

### Get Weather Forecast

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "5 day forecast for Paris"}],
        "messageId": "msg-2"
      }
    }
  }'
```

### Compare Two Cities

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Compare Tokyo and New York weather"}],
        "messageId": "msg-3"
      }
    }
  }'
```

### Get Recommendations

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "4",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What should I wear in Seattle today?"}],
        "messageId": "msg-4"
      }
    }
  }'
```

## 🚀 Deployment

### Render (Recommended - Free Tier)

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. New → Web Service → Connect GitHub repo
4. Add environment variables:
   - `OPENWEATHER_API_KEY`
   - `GEMINI_API_KEY`
5. Deploy!

### Docker

```bash
docker build -t a2a-weather-agent .
docker run -p 8000:8000 \
  -e OPENWEATHER_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  a2a-weather-agent
```

### Railway

```bash
railway login
railway init
railway add
railway variables set OPENWEATHER_API_KEY=your_key
railway variables set GEMINI_API_KEY=your_key
railway up
```

## 📁 Project Structure

```
a2a-weather-agent/
├── main.py              # A2A server entry point with AgentCard
├── weather_client.py    # OpenWeatherMap API client
├── weather_agent.py     # AI-powered weather agent with skills
├── agent_executor.py    # A2A protocol bridge
├── test_client.py       # Test client
├── requirements.txt     # Dependencies
├── Dockerfile          # Container config
├── render.yaml         # Render deployment
├── .env.example        # Environment template
└── README.md           # This file
```

## 🤝 A2A Multi-Agent Integration

This Weather Agent can integrate with other A2A agents:

```
┌─────────────────┐       A2A       ┌─────────────────┐
│   Travel        │ ◀──────────────▶│   Weather       │
│   Planner Agent │                 │   Agent         │
└─────────────────┘                 └─────────────────┘
        │                                   │
        │ "Check weather                    │
        │  for trip dates"                  │
        ▼                                   ▼
┌───────────────────────────────────────────────────────┐
│  Travel Agent: "Planning trip to Paris next week"     │
│  Weather Agent: "Expect 15-20°C, light rain Tuesday"  │
│  Travel Agent: "Pack light jacket, umbrella"          │
└───────────────────────────────────────────────────────┘
```

### Example Use Cases

1. **Travel Planning Agent** → queries weather for destinations
2. **Event Planning Agent** → checks outdoor event feasibility
3. **Agriculture Agent** → monitors weather for farming decisions
4. **Sports Agent** → determines game day conditions

## 🔧 Customization

### Adding New Cities Support

The agent uses OpenWeatherMap's geocoding, so it supports:
- City names: `"London"`, `"Tokyo"`, `"New York"`
- City + Country: `"Paris,FR"`, `"London,UK"`, `"Sydney,AU"`
- City + State (US): `"Portland,OR,US"`, `"Springfield,IL,US"`

### Modifying Temperature Units

Edit `weather_client.py`:
```python
# Change default from metric to imperial
async def get_current_weather(self, city: str, units: str = "imperial"):
```

### Adding New Skills

1. Add method in `weather_agent.py`
2. Add intent pattern in `agent_executor.py`
3. Add skill to `main.py` AgentCard

## 📊 API Rate Limits

**OpenWeatherMap Free Tier:**
- 60 API calls/minute
- 1,000,000 calls/month
- Current weather, 5-day forecast, air quality

**Gemini Free Tier:**
- 60 requests/minute
- 1,500 requests/day

## 📚 Resources

- [A2A Protocol](https://a2a-protocol.org/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [Google Gemini API](https://ai.google.dev/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)

## 📄 License

MIT License
