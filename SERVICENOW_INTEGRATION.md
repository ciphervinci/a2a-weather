# ServiceNow A2A Integration Guide

This guide explains how to connect the Weather A2A Agent to ServiceNow AI Agent Studio.

## Prerequisites

- ServiceNow instance with:
  - Zurich Patch 4+ or Yokohama Patch 11+
  - Now Assist AI Agents 6.0.x+
  - Now Assist SKU (Pro Plus or Enterprise Plus)
- Weather A2A Agent deployed and running

## Quick Reference

| Item | Value |
|------|-------|
| Agent Card URL | `https://a2a-weather.onrender.com/.well-known/agent.json` |
| Agent Execution URL | `https://a2a-weather.onrender.com/` |
| Protocol Version | A2A v0.3 |
| Transport | HTTP (non-streaming) |
| Authentication | API Key (optional) or None |

## Common Issues & Solutions

### Issue 1: HTTP Error 503 - Network Communication Error

**Symptom:**
```json
{
  "error": "Failed to send message: HTTP Error 503: Network communication error: All connection attempts failed"
}
```

**Causes:**
1. **Cold Start Timeout** - Render free tier spins down after 15 minutes of inactivity
2. **Network connectivity** - ServiceNow can't reach the external endpoint
3. **SSL/TLS issues** - Certificate problems

**Solutions:**

#### Solution A: Warm up the service before use
Before sending messages from ServiceNow, hit the health endpoint:
```bash
curl https://a2a-weather.onrender.com/health
```

#### Solution B: Set up a keep-alive ping
Use a service like UptimeRobot, cron-job.org, or Pingdom to ping every 10-14 minutes:
- URL: `https://a2a-weather.onrender.com/health`
- Interval: 10-14 minutes

#### Solution C: Upgrade to Render paid tier ($7/month)
This keeps the service always running without cold starts.

### Issue 2: Request Format Mismatch

**Symptom:** 400 Bad Request or parsing errors

**Cause:** ServiceNow sends a slightly different format than standard JSON-RPC 2.0

**Your curl (works):**
```json
{
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
}
```

**ServiceNow sends:**
```json
{
  "transport": "JSONRPC",
  "method": "message/send",
  "message": {
    "kind": "message",
    "messageId": "msg-xxx",
    "parts": [{"kind": "text", "text": "weather in new london"}],
    "role": "user"
  }
}
```

**Note:** The A2A SDK should handle both formats. If issues persist, check the Render logs.

### Issue 3: Authentication Required

**Symptom:** 401 Unauthorized

**Solution:** Set up API Key authentication:

1. **In Render Dashboard:**
   - Add environment variable: `A2A_API_KEY=your-secure-key-here`
   - Redeploy the service

2. **In ServiceNow:**
   - Create a REST API Key credential with the same key
   - Use header: `x-sn-apikey: your-secure-key-here`

## ServiceNow Configuration Steps

### Step 1: Enable External Agents

1. Go to **AI Agent Studio > Settings**
2. Enable these settings:
   - `sn_aia.external_agents.enabled`: true
   - `sn_aia.internal_agents.enabled_external`: true

### Step 2: Create Connection & Credential Alias

1. Go to **IntegrationHub > Connections & Credential Aliases**
2. Click **New**:
   - Name: `Weather A2A Agent`
   - Type: `Connection and Credential`
   - Connection type: `HTTP`

3. In the **Connections** related list, click **New**:
   - Name: `Weather A2A Connection`
   - Connection URL: `https://a2a-weather.onrender.com`
   - Active: true

### Step 3: Configure Authentication (if using API Key)

1. Go to **IntegrationHub > Credentials**
2. Click **New** and select **Secondary Bot Static Token Credential**:
   - Name: `Weather A2A API Key`
   - Header: `x-sn-apikey`
   - Static Token: `your-api-key-from-render`
   - Active: true

3. Link the credential to your Connection record

### Step 4: Add External Agent

1. Go to **AI Agent Studio > Create and manage > AI agents**
2. Click **Add** dropdown > **External**
3. Select **Agent2Agent (A2A) Protocol**
4. Walk through the guided setup:
   - Provider: Select your Connection Alias
   - Agent Card URL: `https://a2a-weather.onrender.com/.well-known/agent.json`

### Step 5: Test the Connection

Use Postman or curl to verify:

```bash
# Test Agent Card retrieval
curl https://a2a-weather.onrender.com/.well-known/agent.json

# Test message sending
curl -X POST https://a2a-weather.onrender.com/ \
  -H "Content-Type: application/json" \
  -H "x-sn-apikey: your-api-key" \
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

## Debugging

### Check Render Logs

1. Go to your Render dashboard
2. Select the `a2a-weather-agent` service
3. Click **Logs** tab
4. Look for:
   - `[DEBUG] Extracted query:` - Shows what message was received
   - `[DEBUG] Parsed intent:` - Shows how it was interpreted
   - Any error messages

### Enable ServiceNow Debug Logging

Set these system properties:
- `com.snc.platform.security.oauth.debug`: true
- `glide.auth.debug.enabled`: true

Check these tables for logs:
- `sn_aia_execution_plan`
- `sn_aia_external_agent_exec_history`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | Yes | OpenWeatherMap API key |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `A2A_API_KEY` | No | API key for authenticating requests |
| `HOST_URL` | No | Public URL (auto-set by Render) |
| `PORT` | No | Server port (default: 8000) |

## Support

If issues persist:
1. Check Render service logs
2. Verify the agent is responding to curl commands
3. Check ServiceNow Flow Designer execution history
4. Review the A2A protocol specification: https://a2a-protocol.org/latest/
