import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...crud.crud_call_logs import crud_call_logs
from ...schemas.call_logs import CallLogCreate, CallLogUpdate, CallLogRead, CallLogList

router = APIRouter(tags=["call-logs"])

@router.post("/call-logs", response_model=CallLogRead, status_code=status.HTTP_201_CREATED)
async def create_call_log(
    log_in: CallLogCreate,
    db: AsyncSession = Depends(async_get_db),
    # Authentication is removed for this public endpoint
):
    """
    Create a new call log. The conversation data will be uploaded to S3.
    This is a public endpoint intended to be called by the agent backend.
    The owner of the log is determined by the owner of the agent_id provided.
    """
    # The owner_id is now determined by the CRUD layer from the agent_id
    log = await crud_call_logs.create_log(db=db, obj_in=log_in)
    return log

@router.get("/call-logs", response_model=CallLogList)
async def list_call_logs(
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    agent_id: Optional[uuid.UUID] = Query(None, description="Filter logs by a specific agent ID."),
    room_name: Optional[str] = Query(None, description="Search for logs by room name (case-insensitive).")
):
    """
    Get all call logs for the current user's agents, with pagination and optional filters.
    - If agent_id is provided, it returns logs for that specific agent.
    - If room_name is provided, it searches logs by room name.
    - Otherwise, it returns all call logs for the user.
    """
    owner_id = current_user["id"]
    
    if agent_id:
        logs = await crud_call_logs.get_multi_by_agent(
            db=db, owner_id=owner_id, agent_id=agent_id, skip=skip, limit=limit
        )
        total = await crud_call_logs.count_by_agent(db=db, owner_id=owner_id, agent_id=agent_id)
    else:
        logs = await crud_call_logs.get_multi_by_owner(
            db=db, owner_id=owner_id, skip=skip, limit=limit, room_name=room_name
        )
        total = await crud_call_logs.count_by_owner(db=db, owner_id=owner_id, room_name=room_name)
        
    return {"items": logs, "total": total}

@router.get("/call-logs/{log_id}", response_model=CallLogRead)
async def get_call_log(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single call log by its ID.
    """
    owner_id = current_user["id"]
    log = await crud_call_logs.get_log(db=db, id=log_id, owner_id=owner_id)
    if not log:
        raise HTTPException(status_code=404, detail="Call log not found")
    return log

@router.put("/call-logs/{log_id}", response_model=CallLogRead)
async def update_call_log(
    log_id: uuid.UUID,
    log_in: CallLogUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a call log.
    """
    owner_id = current_user["id"]
    updated_log = await crud_call_logs.update_log(db=db, id=log_id, obj_in=log_in, owner_id=owner_id)
    if not updated_log:
        raise HTTPException(status_code=404, detail="Call log not found")
    return updated_log

@router.delete("/call-logs/{log_id}", response_model=CallLogRead, status_code=200) # <-- CORRECTED
async def delete_call_log(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a call log.
    """
    owner_id = current_user["id"]
    deleted_log = await crud_call_logs.delete_log(db=db, id=log_id, owner_id=owner_id)
    if not deleted_log:
        raise HTTPException(status_code=404, detail="Call log not found")
    return deleted_log