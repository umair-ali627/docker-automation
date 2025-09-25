from typing import Dict, Any, List, Optional
from sqlalchemy import Boolean, ForeignKey, String, Text, JSON, Column, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid as uuid_pkg

from ..core.db.database import Base

# Association table for many-to-many relationship between agents and functions
agent_function_association = Table(
    'agent_function_mappings',
    Base.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agent_profiles.id'), primary_key=True),
    Column('function_id', UUID(as_uuid=True), ForeignKey('function_tools.id'), primary_key=True)
)

class FunctionTool(Base):
    """Model for storing function tool definitions."""
    __tablename__ = "function_tools"
    
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    base_url: Mapped[str] = mapped_column(String)
    endpoint_path: Mapped[str] = mapped_column(String)
    function_name: Mapped[str] = mapped_column(String)
    function_description: Mapped[str] = mapped_column(Text)
    http_method: Mapped[str] = mapped_column(String, default="GET")
    headers: Mapped[Dict[str, str]] = mapped_column(JSONB, default_factory=dict)
    parameter_schema: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
    request_template: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_type: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    response_mapping: Mapped[Dict[str, str]] = mapped_column(JSONB, default_factory=dict)
    error_mapping: Mapped[Dict[str, str]] = mapped_column(JSONB, default_factory=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    
    # Relationships
    owner = relationship("User", back_populates="function_tools")
    agent_profiles = relationship(
        "AgentProfile",
        secondary=agent_function_association,
        back_populates="function_tools"
    )