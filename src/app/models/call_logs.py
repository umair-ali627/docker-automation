import uuid as uuid_pkg
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.db.database import Base

class CallLog(Base):
    """Model for storing agent call logs."""
    __tablename__ = "call_logs"

    # --- Fields without default values must come first ---
    room_name: Mapped[str] = mapped_column(String, index=True)
    call_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    agent_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("agent_profiles.id"),
        nullable=False
    )
    owner_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("user.id"),
        nullable=False
    )

    # --- Fields that are nullable (implicitly have a default of None) ---
    call_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    conversation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recording_url: Mapped[Optional[str]] = mapped_column(String, nullable=True) # <-- New field added

    # --- Fields with explicit default values or factories ---
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # <-- Field added
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now(), 
        onupdate=func.now()
    )

    # Relationship to AgentProfile
    agent_profile = relationship("AgentProfile", back_populates="call_logs")
    owner = relationship("User")