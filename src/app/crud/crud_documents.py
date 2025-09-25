from typing import Dict, List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastcrud import FastCRUD
import uuid
import logging

from ..models.document import Document, KnowledgeBase, AgentKnowledgeMapping
from ..schemas.document import (
    DocumentCreate, DocumentCreateInternal, DocumentRead, DocumentUpdate, 
    DocumentUpdateInternal, DocumentDelete,
    KnowledgeBaseCreate, KnowledgeBaseCreateInternal, KnowledgeBaseRead, 
    KnowledgeBaseUpdate, KnowledgeBaseUpdateInternal, KnowledgeBaseDelete,
    AgentKnowledgeMappingCreate, AgentKnowledgeMappingCreateInternal, 
    AgentKnowledgeMappingRead, AgentKnowledgeMappingUpdate, 
    AgentKnowledgeMappingUpdateInternal, AgentKnowledgeMappingDelete
)
# Assuming the qdrant_manager is accessible from this path
from ..core.qdrant_client import qdrant_manager
from ..services.vector_search import vector_search 


logger = logging.getLogger("document-service")

# Create FastCRUD instances
CRUDDocument = FastCRUD[
    Document,
    DocumentCreateInternal,
    DocumentUpdate,
    DocumentUpdateInternal,
    DocumentDelete,
    None
]

CRUDKnowledgeBase = FastCRUD[
    KnowledgeBase,
    KnowledgeBaseCreateInternal,
    KnowledgeBaseUpdate,
    KnowledgeBaseUpdateInternal,
    KnowledgeBaseDelete,
    None
]

CRUDAgentKnowledgeMapping = FastCRUD[
    AgentKnowledgeMapping,
    AgentKnowledgeMappingCreateInternal,
    AgentKnowledgeMappingUpdate,
    AgentKnowledgeMappingUpdateInternal,
    AgentKnowledgeMappingDelete,
    None
]

# Initialize CRUD objects
crud_document = CRUDDocument(Document)
crud_knowledge_base = CRUDKnowledgeBase(KnowledgeBase)
crud_agent_knowledge_mapping = CRUDAgentKnowledgeMapping(AgentKnowledgeMapping)


# Extend with custom methods
class DocumentService:
    async def create_knowledge_base(
        self,
        db: AsyncSession,
        *,
        name: str,
        description: str,
        owner_id: uuid.UUID
    ) -> KnowledgeBase:
        """Create a new knowledge base with a Qdrant collection"""
        # Generate a unique collection name
        collection_name = f"kb_{uuid.uuid4().hex}"
        
        # Create Qdrant collection
        await qdrant_manager.create_collection_if_not_exists(collection_name)
        
        # Create database record
        kb_internal = KnowledgeBaseCreateInternal(
            name=name,
            description=description,
            owner_id=owner_id,
            qdrant_collection=collection_name
        )
        
        return await crud_knowledge_base.create(db=db, object=kb_internal)
    
    async def get_knowledge_bases_by_agent(
        self,
        db: AsyncSession,
        *,
        agent_id: uuid.UUID
    ) -> List[KnowledgeBase]:
        """Get all knowledge bases for an agent"""
        stmt = (
            select(KnowledgeBase)
            .join(
                AgentKnowledgeMapping,
                KnowledgeBase.id == AgentKnowledgeMapping.knowledge_base_id
            )
            .where(AgentKnowledgeMapping.agent_profile_id == agent_id)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_knowledge_bases_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: uuid.UUID
    ) -> List[KnowledgeBase]:
        """Get all knowledge bases for an owner"""
        stmt = select(KnowledgeBase).where(KnowledgeBase.owner_id == owner_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_knowledge_base(
        self,
        db: AsyncSession,
        *,
        kb_id: uuid.UUID
    ) -> bool:
        """Delete a knowledge base and its Qdrant collection"""
        # Get the knowledge base
        kb = await crud_knowledge_base.get(db=db, id=kb_id)
        if not kb:
            return False
        
        # Delete the Qdrant collection
        try:
            qdrant_manager.client.delete_collection(kb["qdrant_collection"])
        except Exception as e:
            # Log the error but continue with database deletion
            logger.error(f"Error deleting Qdrant collection: {e}")
        
        # Delete from database
        await crud_knowledge_base.delete(db=db, id=kb_id)
        
        return True

    async def get_documents_by_knowledge_base(
        self,
        db: AsyncSession,
        *,
        kb_id: uuid.UUID
    ) -> List[Document]:
        """Get all documents for a specific knowledge base"""
        stmt = select(Document).where(Document.knowledge_base_id == kb_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_document(
        self,
        db: AsyncSession,
        *,
        kb_id: uuid.UUID,
        doc_id: uuid.UUID
    ) -> bool:
        """Delete a single document and its associated vector embeddings."""
        doc = await crud_document.get(db=db, id=doc_id)
        
        if not doc or doc["knowledge_base_id"] != kb_id:
            return False

        kb = await crud_knowledge_base.get(db=db, id=kb_id)
        if not kb:
            return False

        try:
            await qdrant_manager.delete_points_by_doc_id(
                collection_name=kb["qdrant_collection"],
                doc_id=str(doc_id)
            )
        except Exception as e:
            logger.error(f"Error deleting points from Qdrant for doc_id {doc_id}: {e}")

        await crud_document.delete(db=db, id=doc_id)
        return True


document_service = DocumentService()