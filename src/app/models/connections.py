from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, ForeignKey, JSON as JSONB, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.db.database import Base
import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID


class Connection(Base):
    """Model for storing voice call connections."""
    __tablename__ = "connections"
    
    # Connection-specific fields
    # room_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    room_id: Mapped[str] = mapped_column(String, primary_key=True)
    call_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)


    # agent_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_profiles.id"))
    agent_id = Column(
        UUID(as_uuid=True),
        # Add the ON DELETE CASCADE rule here
        ForeignKey("agent_profiles.id", ondelete="CASCADE"),
        nullable=False
    )

    # Agent profile fields (duplicated for connection)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    greeting: Mapped[str] = mapped_column(String)
    owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    
    # Provider IDs
    llm_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("llm_providers.id"), 
        nullable=False
    )
    tts_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("tts_providers.id"), 
        nullable=False
    )
    stt_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("stt_providers.id"), 
        nullable=False
    )
    
    # Configuration fields
    llm_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    tts_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    stt_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    allow_interruptions: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    interrupt_speech_duration: Mapped[float] = mapped_column(Float, default=0.5)
    interrupt_min_words: Mapped[int] = mapped_column(Integer, default=0)
    min_endpointing_delay: Mapped[float] = mapped_column(Float, default=0.5)
    max_endpointing_delay: Mapped[float] = mapped_column(Float, default=6.0)
    max_nested_function_calls: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_record: Mapped[bool] = mapped_column(Boolean, default=False) # <-- Field added
    knowledge_bases_data: Mapped[list] = mapped_column(JSONB, default_factory=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
    
    # Relationships
    agent_profile = relationship("AgentProfile", foreign_keys=[agent_id])
    owner = relationship("User", foreign_keys=[owner_id])
    llm_provider = relationship("LLMProvider", foreign_keys=[llm_provider_id])
    tts_provider = relationship("TTSProvider", foreign_keys=[tts_provider_id])
    stt_provider = relationship("STTProvider", foreign_keys=[stt_provider_id])