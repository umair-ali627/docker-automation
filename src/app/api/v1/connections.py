from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from ...services.sip_factory import sip_factory # Adjust this import path

from ...schemas.agent_profile import (
    AgentProfile,
    AgentProfileCreate,
    AgentProfileInDB,
    AgentProfileUpdate,
    AgentProfileList,
)
from ...core.db.database import async_get_db
from ...crud.crud_agent_profiles import crud_agent_profiles
from ...api.dependencies import get_current_user
from ...models.user import User
from ...models import AgentProfile


# Connection endpoints
from ...schemas.connections import (
    ConnectionCreateSimple,
    ConnectionInDB,
    ConnectionCreate,
)
from ...crud.crud_connections import crud_connections

router = APIRouter(tags=["connections"])

@router.post("/connections", response_model=ConnectionInDB)
async def create_connection(
    connection_in: ConnectionCreateSimple, # Use the new, simpler schema
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new connection when user hits call button.
    Requires authentication.
    """
    connection = await crud_connections.create_connection(
        db, 
        room_id=connection_in.room_id, 
        agent_id=connection_in.agent_id, 
        owner_id=current_user["id"]
    )

     # 2. Fetch the agent profile needed for dispatching
    agent_profile = await crud_agent_profiles.get(db=db, id=connection_in.agent_id)
    if not agent_profile:
        raise HTTPException(status_code=404, detail="Agent profile not found for dispatch.")

    # 3. Use the sip_factory to dispatch the agent
    try:
        await sip_factory.dispatch_agent_for_connection(
            room_id=connection.room_id, 
            agent_profile=agent_profile
        )
    except Exception as e:
        # If dispatch fails, the DB record is already created.
        # You might want to add logic here to delete or mark it as failed.
        raise HTTPException(status_code=500, detail=f"Failed to dispatch agent: {e}")

    return connection

@router.get("/connections/{room_id}", response_model=ConnectionInDB)
async def get_connection(
    room_id: str,
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get connection details by room_id.
    No authentication required - public endpoint.
    """
    connection = await crud_connections.get_by_room_id(db=db, room_id=room_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection