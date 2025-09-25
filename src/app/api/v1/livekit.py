import logging
import json
import datetime
import uuid

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession

from livekit import api
from livekit.api import AccessToken, VideoGrants
from livekit.protocol.room import CreateRoomRequest, UpdateRoomMetadataRequest

from ...core.db.database import async_get_db

from ...core.config import settings
from ..dependencies import get_current_user
from ...models.user import User
from ...crud.crud_agent_reference import crud_agent_references
from ...schemas.agent_reference import AgentReferenceLookupCreateInternal

logger = logging.getLogger("livekit-api")

router = APIRouter()

class RoomRequest(BaseModel):
    room_name: str
    user_name: Optional[str] = None
    participant_identity: Optional[str] = None
    expires_in: Optional[int] = 3600  # Default token validity: 1 hour

class AgentRoomRequest(BaseModel):
    room_name: str
    user_name: Optional[str] = None
    participant_identity: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    
class TokenResponse(BaseModel):
    token: str
    room_name: str
    participant_identity: str

async def create_or_get_room(room_name: str, metadata: Optional[dict] = None) -> None:
    """Create a room if it doesn't exist and optionally set metadata."""
    from livekit.protocol.room import CreateRoomRequest, ListRoomsRequest

    try:
        # Make sure the LiveKit URL is properly formatted
        livekit_url = settings.LIVEKIT_HOST
        if not livekit_url.startswith(("http://", "https://")):
            livekit_url = f"https://{livekit_url}"
            logger.info(f"Added https:// prefix to LiveKit URL: {livekit_url}")
        
        lk_api = api.LiveKitAPI(
            url=livekit_url,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        
        # Try to list rooms and check if our room exists
        room_exists = False
        try:
            list_request = ListRoomsRequest()
            response = await lk_api.room.list_rooms(list_request)
            room_exists = any(room.name == room_name for room in response.rooms)
        except Exception as e:
            logger.warning(f"Error checking if room exists: {str(e)}")
        
        if room_exists:
            logger.debug(f"Room already exists: {room_name}")
            # If metadata is provided, update the room metadata
            if metadata:
                update_request = UpdateRoomMetadataRequest(
                    room=room_name,
                    metadata=json.dumps(metadata)
                )
                await lk_api.room.update_room_metadata(update_request)
                logger.info(f"Updated metadata for room: {room_name}")
            return
        
        # Room doesn't exist, create it
        logger.info(f"Creating new room: {room_name}")
        
        # Create a proper CreateRoomRequest
        create_request = CreateRoomRequest()
        create_request.name = room_name
        create_request.empty_timeout = 300  # 5 minutes timeout
        create_request.max_participants = 10
        
        # Set metadata if provided
        if metadata:
            create_request.metadata = json.dumps(metadata)
        
        await lk_api.room.create_room(create_request)
        logger.info(f"Room created successfully: {room_name}")
            
    except Exception as e:
        logger.error(f"Error managing LiveKit room: {e}")
        raise HTTPException(status_code=500, detail=f"Error managing LiveKit room: {str(e)}")


@router.get("/api/token")
async def get_token(
    identity: str = Query(...),
    name: str = Query(...),
    roomName: str = Query(None),
    agent_id: Optional[uuid.UUID] = Query(None),  # Changed to UUID
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    db: AsyncSession = Depends(async_get_db),
):
    """Simple token endpoint compatible with useToken hook from LiveKit components"""
    
    # Generate a unique room ID for this session
    room_uuid = uuid.uuid4()
    
    # Use the provided agent_id or fall back to a default if needed
    agent_uuid = agent_id
    # agent_uuid = "8d54d6e5-98c5-468a-a211-9e7c981770e6"
    if agent_uuid is None:
        # Try to get the default agent profile
        from ...crud.crud_agent_profiles import crud_agent_profiles
        default_agent = await crud_agent_profiles.get_default(db)
        if default_agent:
            agent_uuid = default_agent.id
        else:
            # No default agent found
            logger.warning("No default agent found and no agent_id provided")
    
    if agent_uuid:
        logger.info(f"Token requested for room: {room_uuid}, identity: {identity}, name: {name}, agent: {agent_uuid}")
        
        # Create agent reference entry in database
        try:
            agent_reference_internal = AgentReferenceLookupCreateInternal(
                roomid=room_uuid,
                agentid=agent_uuid
            )
            
            await crud_agent_references.create(db=db, object=agent_reference_internal)
        except Exception as e:
            logger.error(f"Failed to create agent reference: {e}")
    else:
        logger.info(f"Token requested for room: {room_uuid}, identity: {identity}, name: {name}, no agent specified")
    
    # Create or get room directly (not in background) to ensure it exists before generating token
    try:
        # Pass the room UUID as string for room name
        await create_or_get_room(str(room_uuid))
    except Exception as e:
        logger.error(f"Room creation failed: {e}")
        # Continue anyway to at least return a token
    
    try:
        # Create access token
        token = AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        
        # Set identity and name
        token.with_identity(identity)
        token.with_name(name)
        
        # Set token permissions
        grants = VideoGrants(
            room=str(room_uuid),  # Use the generated room UUID
            room_join=True,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
        token.with_grants(grants)
        
        # Default expiration: 24 hours
        token.with_ttl(datetime.timedelta(hours=24))
        
        jwt_token = token.to_jwt()
        logger.debug(f"Generated token for {identity} in room {room_uuid}")
        
        # Return JSON with accessToken field as expected by useToken hook
        # Also include room information for client reference
        return {
            "accessToken": jwt_token,
            "roomName": str(room_uuid),
            "agentId": str(agent_uuid) if agent_uuid else None
        }
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")


@router.post("/token", response_model=TokenResponse)
async def create_token(
    request: RoomRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
) -> TokenResponse:
    """Create a LiveKit token for a room."""
    # Use provided identity or generate from user
    participant_identity = request.participant_identity or f"user_{current_user['id']}"
    user_name = request.user_name or current_user['name'] or current_user['email']
    
    # Create or get room in the background
    background_tasks.add_task(create_or_get_room, request.room_name)
    
    # Create access token
    token = AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    
    # Set identity and name
    token.with_identity(participant_identity)
    token.with_name(user_name)
    
    # Set token permissions
    grants = VideoGrants(
        room=request.room_name,
        room_join=True,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    token.with_grants(grants)
    
    # Set expiration if provided
    if request.expires_in:
        import datetime
        token.with_ttl(datetime.timedelta(seconds=request.expires_in))
    
    return TokenResponse(
        token=token.to_jwt(),
        room_name=request.room_name,
        participant_identity=participant_identity
    )

@router.post("/agent-room", response_model=TokenResponse)
async def create_agent_room(
    request: AgentRoomRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(async_get_db),
) -> TokenResponse:
    """Create a room with a voice agent and return a token for the user."""
    from livekit.agents import cli
    from ...core.livekit_worker import worker_process
    
    if worker_process is None:
        raise HTTPException(
            status_code=500,
            detail="LiveKit worker is not initialized. Make sure LIVEKIT_ENABLE_WORKER is set to true."
        )
    
    # Use provided identity or generate from user
    participant_identity = request.participant_identity or f"user_{current_user['id']}"
    user_name = request.user_name or current_user['name'] or current_user['email']
    
    # Generate a unique room UUID
    room_uuid = uuid.uuid4()
    room_name = str(room_uuid)
    
    # Try to get the agent ID or use default
    agent_uuid = request.agent_id
    if agent_uuid is None:
        # Try to get the default agent profile
        from ...crud.crud_agent_profiles import crud_agent_profiles
        default_agent = await crud_agent_profiles.get_default(db)
        if default_agent:
            agent_uuid = default_agent.id
        else:
            # No default agent found
            logger.warning("No default agent found and no agent_id provided")
    
    # Create agent reference if we have an agent_uuid
    if agent_uuid:
        logger.info(f"Creating agent room with agent ID: {agent_uuid}")
        try:
            agent_reference_internal = AgentReferenceLookupCreateInternal(
                roomid=room_uuid,
                agentid=agent_uuid
            )
            await crud_agent_references.create(db=db, object=agent_reference_internal)
        except Exception as e:
            logger.error(f"Failed to create agent reference: {e}")
    
    # Set metadata if agent ID is specified
    metadata = None
    if agent_uuid:
        metadata = {"agent_id": str(agent_uuid)}
    
    # Create or get room
    await create_or_get_room(room_name, metadata)
    
    # Create access token for the user
    token = AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    
    # Set identity and name
    token.with_identity(participant_identity)
    token.with_name(user_name)
    
    # Set token permissions
    grants = VideoGrants(
        room=room_name,
        room_join=True,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    token.with_grants(grants)
    
    # Create a job to start an agent in this room
    # Will use the agent's entrypoint defined in workers/voice_agent.py
    try:
        from ...core.livekit_worker import worker
        if worker:
            # Simulate a job instead of actually registering with LiveKit dispatcher
            background_tasks.add_task(
                worker.simulate_job,
                room=room_name,
                participant_identity=None
            )
            logger.info(f"Requested agent job for room: {room_name}")
        else:
            logger.error("Worker is not initialized")
    except Exception as e:
        logger.error(f"Failed to create agent job: {e}")
        # Don't fail the request, still return token even if agent creation has issues
        # User can still join the room
    
    return TokenResponse(
        token=token.to_jwt(),
        room_name=room_name,
        participant_identity=participant_identity
    )