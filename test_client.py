"""
Test Client for the A2A Weather Agent

Usage:
    python test_client.py [--url http://localhost:8000]
"""
import argparse
import json
import httpx
import uuid


def get_agent_card(base_url: str) -> dict:
    """Fetch the agent card from the server."""
    url = f"{base_url}/.well-known/agent.json"
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    return response.json()


def send_message(base_url: str, message: str) -> dict:
    """Send a message to the A2A agent."""
    request_body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": str(uuid.uuid4()),
            }
        }
    }
    
    response = httpx.post(
        base_url,
        json=request_body,
        headers={"Content-Type": "application/json"},
        timeout=60.0
    )
    response.raise_for_status()
    return response.json()


def extract_response_text(response: dict) -> str:
    """Extract the text response from the JSON-RPC response."""
    try:
        result = response.get("result", {})
        
        # Check for parts in the result
        if "parts" in result:
            parts = result["parts"]
            for part in parts:
                if part.get("kind") == "text":
                    return part.get("text", "")
        
        # Check for messages array
        if "messages" in result:
            messages = result["messages"]
            if messages:
                last_message = messages[-1]
                parts = last_message.get("parts", [])
                for part in parts:
                    if part.get("kind") == "text":
                        return part.get("text", "")
        
        # Check for artifacts
        if "artifacts" in result:
            artifacts = result["artifacts"]
            if artifacts:
                for artifact in artifacts:
                    parts = artifact.get("parts", [])
                    for part in parts:
                        if part.get("kind") == "text":
                            return part.get("text", "")
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error parsing response: {e}"


def main():
    parser = argparse.ArgumentParser(description="Test client for A2A Weather Agent")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    args = parser.parse_args()
    
    base_url = args.url.rstrip("/")
    
    print("=" * 70)
    print("☀️  A2A Weather Agent - Test Client")
    print("=" * 70)
    
    # Fetch agent card
    print("\n📇 Fetching Agent Card...")
    try:
        agent_card = get_agent_card(base_url)
        print(f"   ✅ Name: {agent_card.get('name')}")
        print(f"   ✅ Version: {agent_card.get('version')}")
        print(f"   ✅ Skills: {len(agent_card.get('skills', []))}")
        for skill in agent_card.get('skills', []):
            print(f"      • {skill['name']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test messages
    test_messages = [
        ("Help", ""),
        ("Current Weather", "Weather in London"),
        ("Weather Forecast", "3 day forecast for Tokyo"),
        ("Compare Cities", "Compare Paris and Berlin weather"),
        ("Natural Language", "Is it a good day to go outside in New York?"),
    ]
    
    for test_name, msg in test_messages:
        print(f"\n{'='*70}")
        print(f"📤 Test: {test_name}")
        print(f"   Message: '{msg or '(empty)'}'")
        print("-" * 70)
        
        try:
            response = send_message(base_url, msg)
            text = extract_response_text(response)
            
            # Truncate long responses
            if len(text) > 800:
                print(f"📥 Response (truncated):\n{text[:800]}...")
            else:
                print(f"📥 Response:\n{text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("✅ Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
