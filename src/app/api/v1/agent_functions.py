from typing import Dict, List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user, get_current_superuser
from ...crud.crud_function_tool import crud_function_tools
from ...crud.crud_agent_profiles import crud_agent_profiles
from ...schemas.function_tool import (
    AgentFunctionAssignment,
    FunctionToolRead,
    FunctionToolList
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/functions", tags=["agent-functions"])

@router.post("/", status_code=status.HTTP_200_OK)
async def assign_functions_to_agent(
    agent_id: UUID,
    assignment: AgentFunctionAssignment,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db)
):
    """
    Assign function tools to an agent profile.
    """
    # Check if agent exists and belongs to the user
    agent = await crud_agent_profiles.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent profile not found"
        )
    
    if agent.owner_id != current_user["id"] and not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this agent profile"
        )
    
    # Check if all functions exist and user has access to them
    for func_id in assignment.function_ids:
        logger.info(f"Checking function {func_id}")
        func = await crud_function_tools.get(db=db, id=func_id)
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Function tool with ID {func_id} not found"
            )
        
        # Check if user has access to the function
        if func.owner_id != current_user["id"] and not func.is_public:
            if not current_user.get("is_superuser", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to use function tool {func.name}"
                )
    
    # Assign functions to agent
    await crud_function_tools.assign_to_agent(
        db=db,
        agent_id=agent_id,
        function_ids=assignment.function_ids
    )
    
    return {"message": "Functions assigned successfully"}

@router.get("/", response_model=FunctionToolList)
async def get_agent_functions(
    agent_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db)
) -> FunctionToolList:
    """
    Get the function tools assigned to an agent profile.
    """
    # Check if agent exists and belongs to the user
    agent = await crud_agent_profiles.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent profile not found"
        )
    
    if agent.owner_id != current_user["id"] and not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this agent profile"
        )
    
    # Get assigned functions
    functions = await crud_function_tools.get_agent_functions(db=db, agent_id=agent_id)
    
    return FunctionToolList(
        items=functions,
        total=len(functions)
    )

@router.delete("/{function_id}", status_code=status.HTTP_200_OK)
async def remove_function_from_agent(
    agent_id: UUID,
    function_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db)
):
    """
    Remove a function tool from an agent profile.
    """
    # Check if agent exists and belongs to the user
    agent = await crud_agent_profiles.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent profile not found"
        )
    
    if agent.owner_id != current_user["id"] and not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this agent profile"
        )
    
    # Get current functions
    current_functions = await crud_function_tools.get_agent_functions(db=db, agent_id=agent_id)
    
    # Create new list without the function to remove
    new_function_ids = [f.id for f in current_functions if f.id != function_id]
    
    # Reassign the filtered list
    await crud_function_tools.assign_to_agent(
        db=db,
        agent_id=agent_id,
        function_ids=new_function_ids
    )
    
    return {"message": "Function removed successfully"}