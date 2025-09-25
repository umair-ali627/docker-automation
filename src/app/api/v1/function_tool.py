from typing import List, Optional, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...schemas.function_tool import (
    FunctionToolCreate,
    FunctionToolRead,
    FunctionToolUpdate,
    FunctionToolList,
    FunctionToolCreateInternal,
    AgentFunctionAssignment,
    FunctionTestRequest,
    FunctionTestResponse
)
from ...crud.crud_function_tool import crud_function_tools
from ...services.function_executor import function_executor

router = APIRouter(prefix="/functions", tags=["function-tools"])

@router.post("", response_model=FunctionToolRead)
async def create_function_tool(
    tool: FunctionToolCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new function tool.a
    
    ## Make.com Configuration Tips:
    
    When configuring function tools for Make.com webhooks:
    
    1. **Response Handling**: Make.com typically returns a simple "Accepted" text response.
       - Leave `response_mapping` empty (or set to `{}`) to handle this automatically
       - The system will automatically interpret "Accepted" as a successful operation
    
    2. **Request Template**: If using a specific data structure for Make.com:
       - Use the `request_template` field to define your data structure
       - Example: `{"name": "${name}", "phone": "${phone_number}"}`
       - Parameters will be substituted using `${parameter_name}` syntax
    
    3. **Common Configuration Example for Make.com**:
       ```json
       {
         "http_method": "POST",
         "base_url": "https://hook.eu2.make.com",
         "endpoint_path": "/your-webhook-id",
         "headers": {"Content-Type": "application/json"},
         "request_template": {},  // Use empty for direct parameter passing
         "response_mapping": {}   // Leave empty for automatic "Accepted" handling
       }
       ```
    
    The system automatically handles Make.com's "Accepted" response and will return:
    `{"success": true, "message": "Operation accepted"}`
    """
    # Convert to internal model with owner_id
    tool_internal = tool.model_dump()
    tool_internal["owner_id"] = current_user["id"]
    
    # Convert to a proper FunctionToolCreateInternal instance
    internal_model = FunctionToolCreateInternal(**tool_internal)
    
    return await crud_function_tools.create(db=db, object=internal_model)

@router.get("", response_model=FunctionToolList)
async def list_function_tools(
    skip: int = 0,
    limit: int = 100,
    include_public: bool = True,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """List function tools owned by the current user and optionally public tools."""
    try:
        # Fetch tools from the database
        tools = await crud_function_tools.get_multi(
            db=db,
            skip=skip,
            limit=limit,
            owner_id=current_user["id"],
            include_public=include_public
        )
        
        # Tools should be a list of FunctionToolRead models already validated
        # Just construct the response model
        return FunctionToolList(items=tools, total=len(tools))
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving function tools: {str(e)}"
        )

@router.get("/{tool_id}", response_model=FunctionToolRead)
async def get_function_tool(
    tool_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific function tool."""
    tool = await crud_function_tools.get(db=db, id=tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Function tool not found")
    
    # Check if user is owner or tool is public
    if tool.owner_id != current_user["id"] and not tool.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this function tool")
    
    return tool

@router.put("/{tool_id}", response_model=FunctionToolRead)
async def update_function_tool(
    tool_update: FunctionToolUpdate,
    tool_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a function tool."""
    tool = await crud_function_tools.get(db=db, id=tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Function tool not found")
    
    if tool.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this function tool")
        
    return await crud_function_tools.update(
        db=db, 
        id=tool_id, 
        object=tool_update,
        owner_id=current_user["id"]
    )

# @router.delete("/{tool_id}", response_model=FunctionToolRead)
# async def delete_function_tool(
#     tool_id: uuid.UUID = Path(...),
#     db: AsyncSession = Depends(async_get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     """Delete a function tool."""
#     tool = await crud_function_tools.get(db=db, id=tool_id)
    
#     if not tool:
#         raise HTTPException(status_code=404, detail="Function tool not found")
    
#     if tool.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not authorized to delete this function tool")
    
#     return await crud_function_tools.delete(db=db, id=tool_id)

@router.delete("/{tool_id}", status_code=204)
async def delete_function_tool(
    tool_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a function tool."""
    tool = await crud_function_tools.get(db=db, id=tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Function tool not found")

    if tool.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this function tool")

    await crud_function_tools.delete(db=db, id=tool_id)
    return  # 204 No Content

@router.post("/{tool_id}/test", response_model=FunctionTestResponse)
async def test_function_tool(
    request: FunctionTestRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """Test execute a function tool."""
    tool = await crud_function_tools.get(db=db, id=request.function_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Function tool not found")
    
    # Check if user is owner or tool is public
    if tool.owner_id != current_user["id"] and not tool.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this function tool")
    
    # Execute the function
    result = await function_executor.execute_function(
        function_id=tool.id,
        parameters=request.parameters
    )
    
    return result
