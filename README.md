# ☀️ A2A Weather AI Agent

An [A2A Protocol](https://a2a-protocol.org/) compliant weather agent that integrates seamlessly with **ServiceNow AI Agent Studio** and other A2A-compatible platforms.

![A2A Protocol](https://img.shields.io/badge/A2A-v0.3-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Features

| Skill | Description | Example Query |
|-------|-------------|---------------|
| **Current Weather** | Real-time weather conditions | `"Weather in London"` |
| **Weather Forecast** | Up to 5-day forecast | `"5 day forecast Tokyo"` |
| **Air Quality** | AQI and pollution levels | `"Air quality in Delhi"` |
| **Recommendations** | AI-powered clothing/activity suggestions | `"What to wear in Paris"` |
| **Compare Cities** | Side-by-side weather comparison | `"Compare London vs Paris"` |
| **Weather Summary** | Complete weather report | `"Weather summary Sydney"` |
| **Natural Language** | Ask anything about weather | `"Good day for hiking?"` |

## 🏗️ Architecture

```
┌─────────────────────┐         A2A Protocol         ┌─────────────────────┐
│                     │◄──────────────────────────────│                     │
│  ServiceNow         │         JSON-RPC 2.0         │  Weather A2A Agent  │
│  AI Agent Studio    │──────────────────────────────►│  (This Project)     │
│                     │           HTTPS              │                     │
└─────────────────────┘                              └──────────┬──────────┘
                                                                │
                                                     ┌──────────┴──────────┐
                                                     │                     │
                                              ┌──────▼──────┐      ┌───────▼──────┐
                                              │ OpenWeather │      │  Gemini AI   │
                                              │     API     │      │     API      │
                                              └─────────────┘      └──────────────┘
```

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
```

Edit `.env` with your API keys:
```bash
OPENWEATHER_API_KEY=your_openweather_key
GEMINI_API_KEY=your_gemini_key

# For production deployment
HOST_URL=https://your-service.onrender.com
```

### 4. Run Locally

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

## ☁️ Deploy to Render

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

### Step 2: Create Render Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `a2a-weather-agent`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

### Step 3: Add Environment Variables

In Render Dashboard → Environment, add:

| Variable | Value | Required |
|----------|-------|----------|
| `OPENWEATHER_API_KEY` | Your OpenWeather key | ✅ Yes |
| `GEMINI_API_KEY` | Your Gemini key | ✅ Yes |
| `HOST_URL` | `https://your-service.onrender.com` | ✅ Yes |
| `A2A_API_KEY` | Your secure API key | Optional |

> ⚠️ **Critical:** You MUST set `HOST_URL` to your public Render URL, otherwise the Agent Card will return internal addresses that ServiceNow cannot reach.

### Step 4: Deploy

Click **Save Changes** and Render will automatically deploy.

### Step 5: Verify Deployment

```bash
# Check health
curl https://your-service.onrender.com/health

# Check Agent Card
curl https://your-service.onrender.com/.well-known/agent.json

# Test message
curl -X POST https://your-service.onrender.com/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
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

## 🔗 ServiceNow Integration

### Prerequisites

- ServiceNow instance with **Zurich Patch 4+** or **Yokohama Patch 11+**
- **Now Assist AI Agents 6.0.x+**
- Now Assist SKU (Pro Plus or Enterprise Plus)

### Configuration Steps

#### 1. Enable External Agents

Go to **AI Agent Studio → Settings** and enable:
- `sn_aia.external_agents.enabled`: **true**
- `sn_aia.internal_agents.enabled_external`: **true**

#### 2. Create Connection Alias

1. Go to **IntegrationHub → Connections & Credential Aliases**
2. Click **New**:
   - **Name:** `Weather A2A Agent`
   - **Type:** Connection and Credential
   - **Connection type:** HTTP

3. In **Connections** related list, click **New**:
   - **Name:** `Weather A2A Connection`
   - **Connection URL:** `https://your-service.onrender.com`
   - **Active:** true

#### 3. Add External Agent

1. Go to **AI Agent Studio → Create and manage → AI agents**
2. Click **Add** → **External**
3. Select **Agent2Agent (A2A) Protocol**
4. Configure:
   - **Provider:** Select your Connection Alias
   - **Agent Card URL:** `https://your-service.onrender.com/.well-known/agent.json`

### Optional: API Key Authentication

For production, add authentication:

1. **In Render:** Add `A2A_API_KEY=your-secure-key` environment variable

2. **In ServiceNow:** Create a credential:
   - Go to **IntegrationHub → Credentials**
   - Select **Secondary Bot Static Token Credential**
   - **Header:** `x-sn-apikey`
   - **Static Token:** `your-secure-key`

## 📡 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent.json` | GET | Agent Card (A2A discovery) |
| `/` | POST | Message endpoint (A2A execution) |
| `/health` | GET | Health check |

### A2A Message Format

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Weather in London"}],
      "messageId": "unique-message-id"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "parts": [
      {
        "kind": "text",
        "text": "☀️ **Current Weather in London, GB**\n..."
      }
    ]
  }
}
```

## 🔧 Troubleshooting

### 503 Network Error from ServiceNow

**Cause:** Agent Card returns internal URL (`http://0.0.0.0:10000/`)

**Fix:** Set `HOST_URL` environment variable in Render to your public URL:
```
HOST_URL=https://your-service.onrender.com
```

### Cold Start Timeouts (Free Tier)

**Cause:** Render free tier spins down after 15 minutes of inactivity

**Solutions:**
1. Set up a keep-alive ping with [UptimeRobot](https://uptimerobot.com) (free)
   - URL: `https://your-service.onrender.com/health`
   - Interval: 10-14 minutes
2. Upgrade to Render Starter plan ($7/month)

### City Not Found

**Cause:** OpenWeatherMap couldn't geocode the city name

**Fix:** Use more specific city names:
- `"Paris,FR"` instead of `"Paris"`
- `"Portland,OR,US"` for US cities with common names

## 📁 Project Structure

```
a2a-weather-agent/
├── main.py                 # A2A server with ServiceNow compatibility
├── weather_client.py       # OpenWeatherMap API client
├── weather_agent.py        # AI-powered weather agent
├── agent_executor.py       # A2A protocol request handler
├── test_client.py          # Test client
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── render.yaml             # Render deployment config
├── .env.example            # Environment template
└── README.md               # This file
```

## 🌐 Multi-Agent Integration

This Weather Agent can integrate with other A2A-compatible agents:

```
┌─────────────────────┐       A2A        ┌─────────────────────┐
│   Travel Planner    │◄────────────────►│   Weather Agent     │
│   Agent             │                  │   (This Project)    │
└─────────────────────┘                  └─────────────────────┘
         │                                        │
         │ "Check weather                         │
         │  for trip dates"                       │
         ▼                                        ▼
┌───────────────────────────────────────────────────────────────┐
│  Travel Agent: "Planning trip to Paris next week"             │
│  Weather Agent: "Expect 15-20°C, light rain Tuesday"          │
│  Travel Agent: "Pack light jacket, umbrella recommended"      │
└───────────────────────────────────────────────────────────────┘
```

### Use Cases

- **Travel Planning Agent** → queries weather for destinations
- **Event Planning Agent** → checks outdoor event feasibility
- **Agriculture Agent** → monitors weather for farming decisions
- **Sports Agent** → determines game day conditions

## 📊 API Rate Limits

| Service | Free Tier Limits |
|---------|------------------|
| OpenWeatherMap | 60 calls/minute, 1M calls/month |
| Google Gemini | 60 requests/minute, 1,500/day |

## 🔒 Security Best Practices

1. **Never commit API keys** - use environment variables
2. **Enable API key authentication** in production
3. **Restrict CORS origins** to your ServiceNow instance
4. **Use HTTPS only** for all communications
5. **Rotate API keys** regularly

## 📚 Resources

- [A2A Protocol Documentation](https://a2a-protocol.org/latest/)
- [ServiceNow A2A Integration Guide](https://www.servicenow.com/community/now-assist-articles/enable-mcp-and-a2a-for-your-agentic-workflows-with-faqs-updated/ta-p/3373907)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [Google Gemini API](https://ai.google.dev/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)

## 📄 License

MIT License - feel free to use and modify for your projects!

---

**Made with ❤️ for the A2A community**
