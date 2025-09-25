# from typing import List
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from ...core.db.database import async_get_db
# from ...models.agent_profile import AgentProfile
# from ...models.document import KnowledgeBase, AgentKnowledgeMapping
# from ...schemas.document import (
#     AgentKnowledgeMappingCreate, 
#     AgentKnowledgeMappingRead,
#     AgentKnowledgeMappingCreateInternal
# )
# from ...models.document import KnowledgeBase, AgentKnowledgeMapping
# from ...crud.crud_documents import crud_agent_knowledge_mapping
# from ...api.dependencies import get_current_user
# from ...models.user import User
# import uuid as uuid_pkg


# router = APIRouter(tags=["agent-knowledge"])

# @router.post("/agent-knowledge", response_model=AgentKnowledgeMappingRead)
# async def associate_knowledge_base(
#     mapping: AgentKnowledgeMappingCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Associate a knowledge base with an agent profile"""
#     # Check if agent profile exists and belongs to user
#     agent_query = select(AgentProfile).where(AgentProfile.id == mapping.agent_profile_id)
#     agent_result = await db.execute(agent_query)
#     agent = agent_result.scalar_one_or_none()
    
#     if not agent:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
        
#     if agent.owner_id != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to modify this agent profile")
    
#     # Check if knowledge base exists and belongs to user
#     kb_query = select(KnowledgeBase).where(KnowledgeBase.id == mapping.knowledge_base_id)
#     kb_result = await db.execute(kb_query)
#     kb = kb_result.scalar_one_or_none()
    
#     if not kb:
#         raise HTTPException(status_code=404, detail="Knowledge base not found")
        
#     if kb.owner_id != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to use this knowledge base")
    
#     # Create association
#     mapping_internal = AgentKnowledgeMappingCreateInternal(
#         agent_profile_id=mapping.agent_profile_id,
#         knowledge_base_id=mapping.knowledge_base_id
#     )
    
#     new_mapping = await crud_agent_knowledge_mapping.create(db=db, object=mapping_internal)
    
#     return new_mapping

# @router.get("/agent-knowledge/{agent_id}", response_model=List[AgentKnowledgeMappingRead])
# async def get_agent_knowledge_bases(
#     agent_id: uuid_pkg.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Get all knowledge bases associated with an agent profile"""
#     # Check if agent profile exists and belongs to user
#     agent_query = select(AgentProfile).where(AgentProfile.id == agent_id)
#     agent_result = await db.execute(agent_query)
#     agent = agent_result.scalar_one_or_none()
    
#     if not agent:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
        
#     if agent.owner_id != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to access this agent profile")
    
#     # Get all mappings
#     mapping_query = select(AgentKnowledgeMapping).where(
#         AgentKnowledgeMapping.agent_profile_id == agent_id
#     )
#     mapping_result = await db.execute(mapping_query)
#     mappings = mapping_result.scalars().all()
    
#     return mappings


from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import uuid as uuid_pkg

from ...core.db.database import async_get_db
from ...models.agent_profile import AgentProfile
from ...models.document import KnowledgeBase, AgentKnowledgeMapping
from ...schemas.document import (
    AgentKnowledgeMappingCreate, 
    AgentKnowledgeMappingRead,
    AgentKnowledgeMappingCreateInternal
)
from ...crud.crud_documents import crud_agent_knowledge_mapping
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(tags=["agent-knowledge"])

@router.post("/agent-knowledge", response_model=AgentKnowledgeMappingRead, status_code=201)
async def associate_knowledge_base(
    mapping: AgentKnowledgeMappingCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """(Endpoint for Frontend) Associate a knowledge base with an agent profile."""
    # 1. Authorize and validate Agent
    agent = await db.get(AgentProfile, mapping.agent_profile_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    if agent.owner_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to modify this agent profile")
    
    # 2. Authorize and validate Knowledge Base
    kb = await db.get(KnowledgeBase, mapping.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    if kb.owner_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to use this knowledge base")

    # 3. CRUCIAL: Check if this mapping already exists
    # FIX: Replaced get_multi with a direct SQLAlchemy query for a more reliable check.
    # This query ensures that BOTH the agent_id AND the kb_id already exist together.
    stmt = select(AgentKnowledgeMapping).where(
        AgentKnowledgeMapping.agent_profile_id == mapping.agent_profile_id,
        AgentKnowledgeMapping.knowledge_base_id == mapping.knowledge_base_id
    )
    result = await db.execute(stmt)
    existing_mapping = result.scalars().first()

    if existing_mapping:
        raise HTTPException(status_code=409, detail="This knowledge base is already assigned to the agent.")
    
    # 4. Create association if it doesn't exist
    mapping_internal = AgentKnowledgeMappingCreateInternal(**mapping.model_dump())
    new_mapping = await crud_agent_knowledge_mapping.create(db=db, object=mapping_internal)
    
    return new_mapping

@router.get("/agent-knowledge/{agent_id}", response_model=List[AgentKnowledgeMappingRead])
async def get_agent_knowledge_bases(
    agent_id: uuid_pkg.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """(Endpoint for Frontend) Get all knowledge base associations for an agent profile."""
    agent = await db.get(AgentProfile, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    if agent.owner_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this agent profile")
    
    # This logic using a direct query is fine and has been kept
    mapping_query = select(AgentKnowledgeMapping).where(
        AgentKnowledgeMapping.agent_profile_id == agent_id
    )
    mapping_result = await db.execute(mapping_query)
    mappings = mapping_result.scalars().all()
    
    return mappings

@router.delete("/agents/{agent_id}/knowledge-bases/{kb_id}", status_code=204)
async def unassign_knowledge_base_from_agent(
    agent_id: uuid_pkg.UUID,
    kb_id: uuid_pkg.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Unassign a knowledge base from an agent.
    This will delete ALL matching records to clean up any existing duplicates.
    """
    agent = await db.get(AgentProfile, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    if agent.owner_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to modify this agent profile")

    # First, check if at least one mapping exists to provide a clean 404
    stmt_select = select(AgentKnowledgeMapping).where(
        AgentKnowledgeMapping.agent_profile_id == agent_id,
        AgentKnowledgeMapping.knowledge_base_id == kb_id
    )
    result = await db.execute(stmt_select)
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Knowledge base is not assigned to this agent.")

    # FIX: Use a direct SQLAlchemy delete statement to remove all matching records,
    # which handles and cleans up any duplicates.
    stmt_delete = delete(AgentKnowledgeMapping).where(
        AgentKnowledgeMapping.agent_profile_id == agent_id,
        AgentKnowledgeMapping.knowledge_base_id == kb_id
    )
    await db.execute(stmt_delete)
    await db.commit()
    
    return Response(status_code=204)