# Add this to your v1/voice_agents.py file

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from ...services.agents import scalable_agent_service
from ...core.config import settings
import httpx

router = APIRouter()

class VoiceSessionRequest(BaseModel):
    room_name: Optional[str] = None  # If None, a random name will be generated
    user_identity: str = "user"
    system_prompt: Optional[str] = None

class VoiceSessionResponse(BaseModel):
    room_name: str
    agent_status: str
    connection_info: Dict[str, str]
    user_token: str

@router.post("/voice-session", response_model=VoiceSessionResponse)
async def create_voice_session(request: VoiceSessionRequest, background_tasks: BackgroundTasks):
    """
    Create a complete voice session with a single API call.
    This handles room creation, agent initialization, and token generation.
    """
    from ...services.agents import normalize_livekit_url
    
    # Generate a room name if not provided
    import uuid
    room_name = request.room_name or f"room-{uuid.uuid4().hex[:8]}"
    
    # 1. Create a room with an agent
    result = await scalable_agent_service.create_agent_for_room(
        room_name=room_name,
        system_prompt=request.system_prompt
    )
    
    # 2. Generate tokens
    agent_token = scalable_agent_service.generate_room_token(
        room_name=room_name, 
        identity="voice-ai-agent"
    )
    
    user_token = scalable_agent_service.generate_room_token(
        room_name=room_name,
        identity=request.user_identity
    )
    
    # 3. Start the agent in the background
    background_tasks.add_task(
        scalable_agent_service.start_agent,
        room_name=room_name,
        token=agent_token,
        system_prompt=request.system_prompt
    )
    
    # 4. Return all the information needed for a client to connect
    # Use the normalized LiveKit URL
    livekit_url = normalize_livekit_url(settings.LIVEKIT_HOST)
    
    return VoiceSessionResponse(
        room_name=room_name,
        agent_status="starting",
        connection_info={
            "livekit_url": livekit_url,
            "room_name": room_name
        },
        user_token=user_token
    )

@router.get("/verify-livekit")
async def verify_livekit_connection():
    """
    Verify connectivity to the LiveKit server
    """
    from ...services.agents import normalize_livekit_url
    
    livekit_host = settings.LIVEKIT_HOST
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET
    
    if not all([livekit_host, api_key, api_secret]):
        raise HTTPException(
            status_code=500, 
            detail="Missing LiveKit configuration (LIVEKIT_HOST, LIVEKIT_API_KEY, or LIVEKIT_API_SECRET)"
        )
    
    # Process the LiveKit host to get proper HTTP and WebSocket URLs
    ws_url = normalize_livekit_url(livekit_host)
    
    # Extract the hostname without protocol for HTTP checks
    if "://" in livekit_host:
        hostname = livekit_host.split("://")[1]
    else:
        hostname = livekit_host
    
    http_url = f"https://{hostname}"
    
    # Verify HTTP connectivity to the LiveKit API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(http_url)
            http_status = response.status_code
    except Exception as e:
        http_status = None
        http_error = str(e)
    else:
        http_error = None
    
    # Verify WebSocket connectivity
    ws_check_url = f"{http_url}/rtc"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Just check if the WebSocket endpoint is reachable via HTTP
            response = await client.get(ws_check_url)
            ws_status = response.status_code
    except Exception as e:
        ws_status = None
        ws_error = str(e)
    else:
        ws_error = None
    
    # Generate a test token and room to check API functionality
    try:
        token = scalable_agent_service.generate_room_token("test-room", "test-user")
        token_test = "success" if token else "failed"
    except Exception as e:
        token_test = f"error: {str(e)}"
    
    return {
        "livekit_host": livekit_host,
        "normalized_ws_url": ws_url,
        "http_connectivity": {
            "url": http_url,
            "status": http_status,
            "error": http_error
        },
        "websocket_connectivity": {
            "url": ws_check_url,
            "status": ws_status,
            "error": ws_error
        },
        "token_generation": token_test,
        "environment_variables": {
            "LIVEKIT_HOST_format": "Correct" if not livekit_host.startswith("https://wss://") and not livekit_host.startswith("http://wss://") else "Incorrect (double protocol)"
        }
    }