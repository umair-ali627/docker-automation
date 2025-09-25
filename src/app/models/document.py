from sqlalchemy import Column, ForeignKey, String, Text, DateTime, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import DateTime as SQLADateTime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from typing import List, Optional
import uuid as uuid_pkg

from ..core.db.database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qdrant_collection: Mapped[str] = mapped_column(String)
    
    # Relationship with owner
    owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    owner = relationship("User", back_populates="knowledge_bases")
    
    # Relationship with documents
    documents = relationship("Document", back_populates="knowledge_base")
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    
    # Relationship with agent profiles
    agent_profiles = relationship(
        "AgentProfile", 
        secondary="agent_knowledge_mappings",
        back_populates="knowledge_bases"
    )


class Document(Base):
    __tablename__ = "documents"
    
    filename: Mapped[str] = mapped_column(String, index=True)
    content_type: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    
    # Relationship with knowledge base - moved up before default columns
    knowledge_base_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete='CASCADE'))
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    # Default value columns below
    created_at: Mapped[DateTime] = mapped_column(SQLADateTime(timezone=True), default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(SQLADateTime(timezone=True), default=func.now(), onupdate=func.now())
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

# This is the correct, modern way to define the model
class AgentKnowledgeMapping(Base):
    __tablename__ = "agent_knowledge_mappings"
    
    agent_profile_id: Mapped[uuid_pkg.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_profiles.id", ondelete="CASCADE"),
        primary_key=True
    )
    knowledge_base_id: Mapped[uuid_pkg.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        primary_key=True
    )