"""
Custom Request Handler for ServiceNow AI Agent Fabric Compatibility

ServiceNow uses a slightly different A2A protocol variant:
- Method: "tasks/send" instead of "message/send"
- Part format: {"type": "text", "text": "..."} instead of {"kind": "text", "text": "..."}

This handler bridges the gap between ServiceNow and the standard A2A SDK.
"""
import json
import uuid
import asyncio
from typing import Any
from starlette.requests import Request
from starlette.responses import JSONResponse

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks import TaskStore
from a2a.types import Message, TextPart


class SimpleEventQueue:
    """Simple event queue to collect agent responses."""
    
    def __init__(self):
        self.events = []
    
    async def enqueue_event(self, event):
        """Add an event to the queue."""
        self.events.append(event)
    
    def get_events(self):
        """Get all collected events."""
        return self.events


class ServiceNowCompatibleHandler:
    """
    A custom handler that wraps the A2A SDK to support ServiceNow's A2A variant.
    
    Key differences handled:
    1. tasks/send -> message/send method mapping
    2. type -> kind field mapping in parts
    3. Response format adaptation
    """
    
    def __init__(self, agent_executor: AgentExecutor, task_store: TaskStore):
        self.agent_executor = agent_executor
        self.task_store = task_store
    
    async def handle_request(self, request: Request) -> JSONResponse:
        """Handle incoming JSON-RPC requests with ServiceNow compatibility."""
        
        try:
            body = await request.body()
            data = json.loads(body)
            
            jsonrpc_id = data.get("id")
            method = data.get("method", "")
            params = data.get("params", {})
            
            print(f"[HANDLER] Received method: {method}")
            
            # Handle tasks/send (ServiceNow variant)
            if method == "tasks/send":
                return await self._handle_tasks_send(jsonrpc_id, params)
            
            # Handle message/send (standard A2A)
            elif method == "message/send":
                return await self._handle_message_send(jsonrpc_id, params)
            
            # Handle tasks/get
            elif method == "tasks/get":
                return await self._handle_tasks_get(jsonrpc_id, params)
            
            # Handle tasks/cancel
            elif method == "tasks/cancel":
                return await self._handle_tasks_cancel(jsonrpc_id, params)
            
            # Method not found
            else:
                return self._error_response(jsonrpc_id, -32601, f"Method not found: {method}")
        
        except json.JSONDecodeError as e:
            return self._error_response(None, -32700, f"Parse error: {str(e)}")
        except Exception as e:
            print(f"[HANDLER ERROR] {str(e)}")
            return self._error_response(jsonrpc_id if 'jsonrpc_id' in dir() else None, -32603, f"Internal error: {str(e)}")
    
    async def _handle_tasks_send(self, jsonrpc_id: str, params: dict) -> JSONResponse:
        """
        Handle ServiceNow's tasks/send method.
        
        ServiceNow format:
        {
            "id": "task-id",
            "sessionId": null,
            "message": {
                "role": null,
                "parts": [{"type": "text", "text": "..."}]
            }
        }
        """
        try:
            task_id = params.get("id", str(uuid.uuid4()))
            session_id = params.get("sessionId") or str(uuid.uuid4())
            message_data = params.get("message", {})
            
            # Extract text from parts (ServiceNow uses "type" instead of "kind")
            text_content = ""
            parts = message_data.get("parts", [])
            for part in parts:
                # Handle both "type" (ServiceNow) and "kind" (standard A2A)
                part_type = part.get("type") or part.get("kind")
                if part_type == "text":
                    text_content = part.get("text", "")
                    break
            
            print(f"[HANDLER] Extracted text: '{text_content}'")
            
            # Create event queue to collect responses
            event_queue = SimpleEventQueue()
            
            # Create a minimal request context
            context = self._create_request_context(text_content, task_id, session_id)
            
            # Execute the agent
            await self.agent_executor.execute(context, event_queue)
            
            # Collect response from event queue
            response_text = ""
            events = event_queue.get_events()
            
            # Extract text from events
            for event in events:
                print(f"[HANDLER] Event type: {type(event).__name__}")
                print(f"[HANDLER] Event attrs: {dir(event)}")
                
                # Try multiple ways to extract text
                # Method 1: parts attribute (Message object)
                if hasattr(event, 'parts') and event.parts:
                    for part in event.parts:
                        print(f"[HANDLER] Part type: {type(part).__name__}")
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            print(f"[HANDLER] Found text in part.text")
                            break
                        # Try root attribute for TextPart
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            response_text = part.root.text
                            print(f"[HANDLER] Found text in part.root.text")
                            break
                
                # Method 2: direct text attribute
                if not response_text and hasattr(event, 'text') and event.text:
                    response_text = event.text
                    print(f"[HANDLER] Found text in event.text")
                
                # Method 3: Try to convert to dict
                if not response_text:
                    try:
                        if hasattr(event, 'model_dump'):
                            event_dict = event.model_dump()
                            print(f"[HANDLER] Event dict: {event_dict}")
                            if 'parts' in event_dict:
                                for part in event_dict['parts']:
                                    if isinstance(part, dict) and 'text' in part:
                                        response_text = part['text']
                                        print(f"[HANDLER] Found text in model_dump")
                                        break
                    except Exception as e:
                        print(f"[HANDLER] model_dump error: {e}")
                
                if response_text:
                    break
            
            print(f"[HANDLER] Response text length: {len(response_text)}")
            print(f"[HANDLER] Response text preview: {response_text[:200] if response_text else 'EMPTY'}")
            
            # Build ServiceNow-compatible response
            # Include both 'message' and 'artifacts' for maximum compatibility
            response = {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": {
                    "id": task_id,
                    "sessionId": session_id,
                    "status": {
                        "state": "completed"
                    },
                    "message": {
                        "role": "agent",
                        "parts": [
                            {
                                "type": "text",
                                "text": response_text
                            }
                        ]
                    },
                    "artifacts": [
                        {
                            "parts": [
                                {
                                    "type": "text",
                                    "text": response_text
                                }
                            ]
                        }
                    ]
                }
            }
            
            print(f"[HANDLER] Full response: {json.dumps(response, indent=2)}")
            
            return JSONResponse(response)
        
        except Exception as e:
            print(f"[HANDLER ERROR] tasks/send: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._error_response(jsonrpc_id, -32603, f"Execution error: {str(e)}")
    
    async def _handle_message_send(self, jsonrpc_id: str, params: dict) -> JSONResponse:
        """Handle standard A2A message/send method."""
        # For standard A2A, we can use similar logic
        # Convert to tasks/send format and reuse
        converted_params = {
            "id": str(uuid.uuid4()),
            "sessionId": params.get("contextId"),
            "message": params.get("message", {}),
        }
        return await self._handle_tasks_send(jsonrpc_id, converted_params)
    
    async def _handle_tasks_get(self, jsonrpc_id: str, params: dict) -> JSONResponse:
        """Handle tasks/get method."""
        task_id = params.get("id")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "id": task_id,
                "status": {
                    "state": "completed"
                }
            }
        })
    
    async def _handle_tasks_cancel(self, jsonrpc_id: str, params: dict) -> JSONResponse:
        """Handle tasks/cancel method."""
        task_id = params.get("id")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "id": task_id,
                "status": {
                    "state": "canceled"
                }
            }
        })
    
    def _create_request_context(self, text: str, task_id: str, session_id: str) -> RequestContext:
        """Create a RequestContext from the extracted text."""
        from a2a.types import Message, TextPart
        
        # Create a message object that the executor can understand
        message = Message(
            role="user",
            parts=[TextPart(text=text)],
            messageId=str(uuid.uuid4()),
        )
        
        # Create RequestContext
        # Note: This is a simplified context - the full SDK context has more fields
        context = RequestContext(
            task_id=task_id,
            context_id=session_id,
        )
        
        # Store the message text for extraction
        context._user_text = text
        context._message = message
        
        return context
    
    def _error_response(self, jsonrpc_id: Any, code: int, message: str) -> JSONResponse:
        """Create a JSON-RPC error response."""
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "error": {
                "code": code,
                "message": message
            }
        })


# Monkey-patch RequestContext to support our custom fields
_original_get_user_input = None

def _patched_get_user_input(self):
    """Patched get_user_input that checks for our custom _user_text field."""
    if hasattr(self, '_user_text') and self._user_text:
        return self._user_text
    # Fall back to original behavior
    if _original_get_user_input:
        return _original_get_user_input(self)
    return ""

# Apply the patch
try:
    from a2a.server.agent_execution import RequestContext as RC
    if hasattr(RC, 'get_user_input'):
        _original_get_user_input = RC.get_user_input
        RC.get_user_input = _patched_get_user_input
except:
    pass
