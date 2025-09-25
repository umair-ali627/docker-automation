from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Knowledge Base Schemas
class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBaseCreate(KnowledgeBaseBase):
    model_config = ConfigDict(extra="forbid")

class KnowledgeBaseCreateInternal(KnowledgeBaseCreate):
    owner_id: uuid.UUID
    qdrant_collection: str

class KnowledgeBaseRead(KnowledgeBaseBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    qdrant_collection: str

class KnowledgeBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    name: Optional[str] = None
    description: Optional[str] = None

class KnowledgeBaseUpdateInternal(KnowledgeBaseUpdate):
    pass

class KnowledgeBaseDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID


# Document Schemas
class DocumentBase(BaseModel):
    filename: str
    content_type: str
    content: str
    knowledge_base_id: uuid.UUID  # Changed to UUID to match KnowledgeBase.id

class DocumentCreate(DocumentBase):
    model_config = ConfigDict(extra="forbid")

class DocumentCreateInternal(DocumentCreate):
    chunk_count: int = 0

class DocumentRead(DocumentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    chunk_count: int

class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    filename: Optional[str] = None
    content: Optional[str] = None
    chunk_count: Optional[int] = None

class DocumentUpdateInternal(DocumentUpdate):
    pass

class DocumentDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID

# Agent Knowledge Mapping Schemas
class AgentKnowledgeMappingBase(BaseModel):
    agent_profile_id: uuid.UUID
    knowledge_base_id: uuid.UUID

class AgentKnowledgeMappingCreate(AgentKnowledgeMappingBase):
    model_config = ConfigDict(extra="forbid")

class AgentKnowledgeMappingCreateInternal(AgentKnowledgeMappingCreate):
    pass

# class AgentKnowledgeMappingRead(AgentKnowledgeMappingBase):
#     id: uuid.UUID

class AgentKnowledgeMappingRead(AgentKnowledgeMappingBase):
    pass

class AgentKnowledgeMappingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    agent_profile_id: Optional[uuid.UUID] = None
    knowledge_base_id: Optional[uuid.UUID] = None 

class AgentKnowledgeMappingUpdateInternal(AgentKnowledgeMappingUpdate):
    pass

class AgentKnowledgeMappingDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID

# Search Schemas
class SearchQuery(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    content: str
    document_id: uuid.UUID  # Changed to UUID to match Document.id
    metadata: Dict[str, Any]
    score: float



# for connection endpoint 
class DocumentWithContentRead(DocumentRead):
    content: str # Override to ensure content is included

class KnowledgeBaseWithDocsRead(KnowledgeBaseRead):
    documents: List[DocumentWithContentRead] = []
    # Exclude qdrant_collection from the final response
    qdrant_collection: Optional[str] = Field(default=None, exclude=True)
