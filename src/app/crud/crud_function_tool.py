from typing import Dict, List, Optional, Any
import uuid
from fastapi import HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastcrud import FastCRUD
import logging

from ..models.function_tool import FunctionTool, agent_function_association
from ..models.agent_profile import AgentProfile
from ..schemas.function_tool import (
    FunctionToolCreate,
    FunctionToolCreateInternal,
    FunctionToolUpdate,
    FunctionToolDelete,
    FunctionToolRead
)

# Create a FastCRUD instance for FunctionTool
CRUDFunctionTool = FastCRUD[
    FunctionTool,
    FunctionToolCreateInternal,
    FunctionToolUpdate,
    FunctionToolUpdate,  # Internal update is the same as external
    FunctionToolDelete,
    FunctionToolRead
]

# Base CRUD object
base_crud = CRUDFunctionTool(FunctionTool)
logger = logging.getLogger("function-tool-crud")

# Extended CRUD class that leverages the base FastCRUD methods better
class ExtendedCRUDFunctionTool:
    def __init__(self):
        self.model = FunctionTool

    # Leverage base FastCRUD methods wherever possible
    async def create(self, db: AsyncSession, *, object: FunctionToolCreateInternal) -> FunctionToolRead:
        """Create a new function tool."""
        # Only custom part: Check if name already exists for this owner
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.name == object.name,
                    self.model.owner_id == object.owner_id
                )
            )
        )
        if result.scalars().first():
            raise HTTPException(status_code=400, detail=f"Function tool with name '{object.name}' already exists")
            
        # Use FastCRUD for the actual creation
        new_tool = await base_crud.create(db=db, object=object)
        return FunctionToolRead.model_validate(new_tool, from_attributes=True)


    async def get(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[FunctionToolRead]:
        """Get a function tool by ID using FastCRUD."""
        obj = await base_crud.get(db=db, id=id)
        print("DEBUG in get all >>>", type(obj), obj)
        logger.info(f"DEBUG in get all >>> {type(obj)} {obj}")
        return FunctionToolRead.model_validate(obj, from_attributes=True) if obj else None

    async def get_by_name(self, db: AsyncSession, name: str, owner_id: uuid.UUID) -> Optional[FunctionToolRead]:
        """Get a function tool by name and owner."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.name == name,
                    self.model.owner_id == owner_id
                )
            )
        )
        tool = result.scalar_one_or_none()
        print("get_by_name tool:", tool)
        print("DEBUG >>>", type(tool), tool)
        logger.info(f"get_by_name tool: {tool}")
        logger.info(f"DEBUG >>> {type(tool)} {tool}")
        return FunctionToolRead.model_validate(tool, from_attributes=True) if tool else None

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        owner_id: Optional[uuid.UUID] = None,
        include_public: bool = True
    ) -> List[FunctionToolRead]:
        """Get multiple function tools, using FastCRUD with additional filters."""
        filters = []
        
        if owner_id is not None:
            if include_public:
                filters.append(or_(
                    self.model.owner_id == owner_id,
                    self.model.is_public == True
                ))
            else:
                filters.append(self.model.owner_id == owner_id)
        elif not include_public:
            # If no owner_id and not including public, return nothing
            return []
            
        # objects = await base_crud.get_multi(db=db, skip=skip, limit=limit, filters=filters)
        # return [FunctionToolRead.model_validate(obj, from_attributes=True) for obj in objects]
    
        # Use the base get_multi with our filters
        result = await base_crud.get_multi(db=db, skip=skip, limit=limit, filters=filters)
        objects = result["data"]
        return [FunctionToolRead.model_validate(obj, from_attributes=True) for obj in objects]

    async def update(
        self,
        db: AsyncSession,
        *,
        id: uuid.UUID,
        object: FunctionToolUpdate,
        owner_id: Optional[uuid.UUID] = None
    ) -> FunctionToolRead:
        """Update a function tool."""
        # Step 1: Fetch the raw SQLAlchemy model instance directly from the database.
        result = await db.execute(select(self.model).where(self.model.id == id))
        db_obj = result.scalar_one_or_none()

        if not db_obj:
            raise HTTPException(status_code=404, detail="Function tool not found")

        # Step 2: Check ownership.
        if owner_id is not None and db_obj.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        # Step 3: If trying to update name, check for duplicates.
        if object.name is not None and object.name != db_obj.name:
            existing = await self.get_by_name(db, object.name, db_obj.owner_id)
            if existing and existing.id != id:
                raise HTTPException(status_code=400, detail=f"Function tool with name '{object.name}' already exists")

        # Step 4: Manually update the fields on the SQLAlchemy object.
        # This is the safest way to prevent data corruption.
        update_data = object.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # Step 5: Commit the changes and refresh the object state.
        await db.commit()
        await db.refresh(db_obj)

        # Step 6: Validate and return the updated object.
        return FunctionToolRead.model_validate(db_obj, from_attributes=True)

    # async def update(
    #     self, 
    #     db: AsyncSession, 
    #     *, 
    #     id: uuid.UUID, 
    #     object: FunctionToolUpdate, 
    #     owner_id: Optional[uuid.UUID] = None
    # ) -> FunctionToolRead:
    #     """Update a function tool."""
    #     # First check if the function exists
    #     db_obj = await self.get(db=db, id=id)
    #     if not db_obj:
    #         raise HTTPException(status_code=404, detail="Function tool not found")
            
    #     # Check ownership if owner_id provided
    #     if owner_id is not None and db_obj.owner_id != owner_id:
    #         raise HTTPException(status_code=403, detail="Not enough permissions")
            
    #     # If trying to update name, check for duplicates
    #     if object.name is not None and object.name != db_obj.name:
    #         existing = await self.get_by_name(db, object.name, db_obj.owner_id)
    #         if existing and existing.id != id:
    #             raise HTTPException(status_code=400, detail=f"Function tool with name '{object.name}' already exists")
                
    #     # Use the FastCRUD update method
    #     updated = await base_crud.update(db=db, id=id, object=object)
    #     return FunctionToolRead.model_validate(updated, from_attributes=True)

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[FunctionToolRead]:
        """Delete a function tool using FastCRUD."""
        # Check if exists first (for better error messages)
        existing = await self.get(db=db, id=id)
        if not existing:
            raise HTTPException(status_code=404, detail="Function tool not found")
            
        deleted = await base_crud.delete(db=db, id=id)
        return FunctionToolRead.model_validate(deleted, from_attributes=True) if deleted else None

    async def assign_to_agent(
    self, 
    db: AsyncSession, 
    *, 
    agent_id: uuid.UUID, 
    function_ids: List[uuid.UUID]
) -> bool:
        """Assign function tools to an agent."""
        from ..models.agent_profile import AgentProfile
        from ..models.function_tool import FunctionTool, agent_function_association
        from sqlalchemy import select, delete
        
        # Check if agent exists using a proper async query
        agent_query = select(AgentProfile).where(AgentProfile.id == agent_id)
        result = await db.execute(agent_query)
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent profile not found")
            
        # Get all the function tools using a proper async query
        function_tools = []
        for func_id in function_ids:
            func_query = select(FunctionTool).where(FunctionTool.id == func_id)
            result = await db.execute(func_query)
            tool = result.scalar_one_or_none()
            
            if not tool:
                raise HTTPException(status_code=404, detail=f"Function tool with ID {func_id} not found")
            function_tools.append(tool)
        
        # First, delete all existing associations for this agent
        delete_stmt = delete(agent_function_association).where(
            agent_function_association.c.agent_id == agent_id
        )
        await db.execute(delete_stmt)
        
        # Then, create new associations
        for tool in function_tools:
            # Insert directly into the association table
            insert_stmt = agent_function_association.insert().values(
                agent_id=agent_id,
                function_id=tool.id
            )
            await db.execute(insert_stmt)
        
        await db.commit()
        return True
        
    async def get_agent_functions(
        self, 
        db: AsyncSession, 
        *, 
        agent_id: uuid.UUID
    ) -> List[FunctionToolRead]:
        """Get function tools assigned to an agent."""
        # First check if agent exists
        agent = await db.get(AgentProfile, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent profile not found")
            
        # Get the functions associated with this agent using a query
        query = select(FunctionTool).join(
            agent_function_association,
            and_(
                agent_function_association.c.function_id == FunctionTool.id,
                agent_function_association.c.agent_id == agent_id
            )
        )
        
        result = await db.execute(query)
        function_tools = list(result.scalars().all())
        return [FunctionToolRead.model_validate(tool, from_attributes=True) for tool in function_tools]

# Create a singleton CRUD instance
crud_function_tools = ExtendedCRUDFunctionTool()