import uuid as uuid_pkg
from sqlalchemy import ForeignKey, String, Text, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Dict, Any, Optional
from enum import Enum as PyEnum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from ..core.db.database import Base

class SIPTrunkType(str, PyEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class SIPCallDirection(str, PyEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class SIPCallStatus(str, PyEnum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class SIPTrunk(Base):
    """Model for storing SIP trunk configurations."""
    __tablename__ = "sip_trunks"
    
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship with owner
    owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    owner = relationship("User", back_populates="sip_trunks")
    
    # SIP configuration
    trunk_type: Mapped[str] = mapped_column(Enum(SIPTrunkType))
    trunk_id: Mapped[str] = mapped_column(String)  # LiveKit trunk ID
    
    # Common fields
    sip_termination_uri: Mapped[str] = mapped_column(String)  # SIP server address
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Optional for inbound
    password: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Optional for inbound
    phone_number: Mapped[str] = mapped_column(String, index=True)
    
    # Other configuration as JSON
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)

    # Soft delete flag
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Primary key
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    
    # Relationships
    agent_mappings = relationship("SIPAgentMapping", back_populates="sip_trunk")


class SIPAgentMapping(Base):
    """Model for linking SIP trunks to agents."""
    __tablename__ = "sip_agent_mappings"
    
    # SIP Trunk reference
    sip_trunk_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sip_trunks.id"))
    
    # Separate agent profiles for inbound and outbound
    inbound_agent_id: Mapped[Optional[uuid_pkg.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("agent_profiles.id"), 
        nullable=True
    )
    outbound_agent_id: Mapped[Optional[uuid_pkg.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("agent_profiles.id"), 
        nullable=True
    )
    
    # LiveKit dispatch rule ID
    dispatch_rule_id: Mapped[str] = mapped_column(String, nullable=True)
    
    # Primary key
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    
    # Relationships - without trying to create backrefs that already exist
    sip_trunk = relationship("SIPTrunk", back_populates="agent_mappings")
    
    # Use the existing relationships from the AgentProfile side
    inbound_agent = relationship(
        "AgentProfile", 
        foreign_keys=[inbound_agent_id],
        primaryjoin="SIPAgentMapping.inbound_agent_id == AgentProfile.id",
        overlaps="inbound_sip_mappings"
    )
    
    outbound_agent = relationship(
        "AgentProfile", 
        foreign_keys=[outbound_agent_id],
        primaryjoin="SIPAgentMapping.outbound_agent_id == AgentProfile.id",
        overlaps="outbound_sip_mappings"
    )

class SIPCall(Base):
    """Model for tracking SIP call details."""
    __tablename__ = "sip_calls"
    
    # PRIMARY KEY AND REQUIRED FIELDS WITHOUT DEFAULTS MUST COME FIRST
    # Call identifiers
    call_id: Mapped[str] = mapped_column(String, index=True)  # LiveKit SIP call ID
    # room_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), index=True)  # Room UUID
    room_id: Mapped[str] = mapped_column(String, index=True)  
    # Change from UUID to String

    # Call metadata (required fields without defaults)
    direction: Mapped[str] = mapped_column(Enum(SIPCallDirection))
    phone_number: Mapped[str] = mapped_column(String, index=True)
    
    # Optional fields without defaults
    trunk_id: Mapped[Optional[uuid_pkg.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sip_trunks.id"), nullable=True)
    agent_id: Mapped[Optional[uuid_pkg.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=True)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # FIELDS WITH DEFAULTS MUST COME LAST (in any order)
    # Status with default value
    status: Mapped[str] = mapped_column(Enum(SIPCallStatus), default=SIPCallStatus.INITIATED)
    
    # Fields with default values
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    call_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
    
    # Primary key with default
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    trunk = relationship("SIPTrunk")
    agent = relationship("AgentProfile")

class TwilioUrlUpdateRequest(BaseModel):
    """
    Pydantic schema for the request body to update a Twilio phone number's voice URL.
    """
    url: str = Field(..., description="The new URL to set for the Twilio phone number's voice configuration.")
    phone_number: str = Field(..., description="The E.164 formatted phone number to update (e.g., '+12693906795').")