# from typing import Dict, Any
# from sqlalchemy import Boolean, ForeignKey, String, Text, Float, Integer, Enum, JSON
# from sqlalchemy.orm import relationship, Mapped, mapped_column
# from ..core.db.database import Base
# from sqlalchemy.dialects.postgresql import UUID, JSONB
# import uuid as uuid_pkg
# from ..schemas.provider_types import LLMProvider, TTSProvider, STTProvider
# from .function_tool import agent_function_association

# class AgentProfile(Base):
#     """Model for storing agent profiles."""
#     __tablename__ = "agent_profiles"
    
#     # Required fields (non-default) must come first
#     name: Mapped[str] = mapped_column(String, index=True)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     system_prompt: Mapped[str] = mapped_column(Text)
#     greeting: Mapped[str] = mapped_column(String)
#     owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    
#     # Fields with defaults must come after
#     id: Mapped[uuid_pkg.UUID] = mapped_column(
#         UUID(as_uuid=True), 
#         primary_key=True, 
#         default_factory=uuid_pkg.uuid4
#     )
#     llm_provider: Mapped[str] = mapped_column(Enum(LLMProvider), default=LLMProvider.OPENAI)
#     tts_provider: Mapped[str] = mapped_column(Enum(TTSProvider), default=TTSProvider.OPENAI)
#     stt_provider: Mapped[str] = mapped_column(Enum(STTProvider), default=STTProvider.DEEPGRAM)
#     llm_options: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
#     tts_options: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
#     stt_options: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
#     allow_interruptions: Mapped[bool] = mapped_column(Boolean, default=True)
#     profile_options: Mapped[Dict[str, Any]] = mapped_column(JSONB, default_factory=dict)
#     interrupt_speech_duration: Mapped[float] = mapped_column(Float, default=0.5)
#     interrupt_min_words: Mapped[int] = mapped_column(Integer, default=0)
#     min_endpointing_delay: Mapped[float] = mapped_column(Float, default=0.5)
#     max_endpointing_delay: Mapped[float] = mapped_column(Float, default=6.0)
#     max_nested_function_calls: Mapped[int] = mapped_column(Integer, default=1)
#     active: Mapped[bool] = mapped_column(Boolean, default=True)
#     is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
#     # Relationships at the end
#     owner = relationship("User", back_populates="agent_profiles")
#     knowledge_bases = relationship(
#         "KnowledgeBase", 
#         secondary="agent_knowledge_mappings",
#         back_populates="agent_profiles"
#     )
    
#     # Define separate relationships for the SIP mappings with overlaps parameter
#     function_tools = relationship(
#         "FunctionTool", 
#         secondary=agent_function_association,
#         back_populates="agent_profiles"
#     )

#     inbound_sip_mappings = relationship(
#         "SIPAgentMapping", 
#         foreign_keys="SIPAgentMapping.inbound_agent_id",
#         primaryjoin="AgentProfile.id == SIPAgentMapping.inbound_agent_id",
#         overlaps="inbound_agent"
#     )
    
#     outbound_sip_mappings = relationship(
#         "SIPAgentMapping", 
#         foreign_keys="SIPAgentMapping.outbound_agent_id",
#         primaryjoin="AgentProfile.id == SIPAgentMapping.outbound_agent_id",
#         overlaps="outbound_agent"
#     )


# class AgentReferenceLookup(Base):
#     __tablename__ = "agent_reference_lookup"
    
#     # Required fields
#     roomid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True))
#     agentid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True))
    
#     # Primary key (has a default, but is a special case)
#     id: Mapped[uuid_pkg.UUID] = mapped_column(
#         UUID(as_uuid=True), 
#         primary_key=True, 
#         default_factory=uuid_pkg.uuid4
#     )

# # Add Tables for TranscriberLibrary, VoiceLibrary
# """
# VoiceLibrary Sample JSON (From Vapi):
# {
#         "id": "fad33df4-53ea-4e0a-87bd-3bd7581c5138",
#         "provider": "openai",
#         "providerId": "fable",
#         "slug": "fable",
#         "name": "fable",
#         "createdAt": "2024-03-23T16:49:49.276Z",
#         "updatedAt": "2024-03-23T16:49:49.276Z",
#         "isPublic": true,
#         "isDeleted": true,
#         "orgId": "aa4c36ba-db21-4ce0-9c6e-bb55a8d2b188"
#     }
# """


from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, ForeignKey, JSON as JSONB, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.db.database import Base
import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from .function_tool import agent_function_association

class AgentProfile(Base):
    """Model for storing agent profiles."""
    __tablename__ = "agent_profiles"
    
    # Required fields (non-default) must come first
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    greeting: Mapped[str] = mapped_column(String)
    owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))

    # Replace enum fields with foreign keys
    llm_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("llm_providers.id"), 
        nullable=True
    )
    tts_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("tts_providers.id"), 
        nullable=True
    )
    stt_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("stt_providers.id"), 
        nullable=True
    )
    
    # Fields with defaults
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
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
    is_record: Mapped[bool] = mapped_column(Boolean, default=False) # <-- New field added
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
        
    # Relationships
    owner = relationship("User", back_populates="agent_profiles")
    llm_provider = relationship("LLMProvider")
    tts_provider = relationship("TTSProvider")
    stt_provider = relationship("STTProvider")
    knowledge_bases = relationship(
        "KnowledgeBase", 
        secondary="agent_knowledge_mappings",
        back_populates="agent_profiles"
    )
    function_tools = relationship(
        "FunctionTool", 
        secondary=agent_function_association,
        back_populates="agent_profiles"
    )
    inbound_sip_mappings = relationship(
        "SIPAgentMapping", 
        foreign_keys="SIPAgentMapping.inbound_agent_id",
        primaryjoin="AgentProfile.id == SIPAgentMapping.inbound_agent_id",
        overlaps="inbound_agent"
    )
    outbound_sip_mappings = relationship(
        "SIPAgentMapping", 
        foreign_keys="SIPAgentMapping.outbound_agent_id",
        primaryjoin="AgentProfile.id == SIPAgentMapping.outbound_agent_id",
        overlaps="outbound_agent"
    )
    # Inside the AgentProfile class
    # CORRECTED: The cascade option has been removed to prevent hard deletes.
    # The application logic now handles soft-deleting the call logs.
    call_logs = relationship("CallLog", back_populates="agent_profile")
    
class AgentReferenceLookup(Base):
    __tablename__ = "agent_reference_lookup"
    
    roomid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True))
    agentid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True))
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )

# Below code is moved to their respective files 

# class LLMProvider(Base):
#     __tablename__ = "llm_providers"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
#     provider = Column(String, unique=True, index=True)  # Added to match schema
#     models = Column(JSONB, default=list)  # List of strings, e.g., ["gpt-4o", ...]

# class TTSProvider(Base):
#     __tablename__ = "tts_providers"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
#     provider = Column(String, unique=True, index=True)  # Added to match schema
#     models = Column(JSONB, default=list)  # List of dicts, e.g., [{"model": "sonic-2", "languages": ["en", ...]}]
#     voices = Column(JSONB, default=list)  # List of dicts, e.g., [{"id": "...", "name": "Brooke", ...}]

# class STTProvider(Base):
#     __tablename__ = "stt_providers"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
#     provider = Column(String, unique=True, index=True)  # Added to match schema
#     models = Column(JSONB, default=list)


# class Connection(Base):
#     """Model for storing voice call connections."""
#     __tablename__ = "connections"
    
#     # Connection-specific fields
#     # room_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
#     room_id: Mapped[str] = mapped_column(String, primary_key=True)

#     # agent_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_profiles.id"))
#     agent_id = Column(
#         UUID(as_uuid=True),
#         # Add the ON DELETE CASCADE rule here
#         ForeignKey("agent_profiles.id", ondelete="CASCADE"),
#         nullable=False
#     )

#     # Agent profile fields (duplicated for connection)
#     name: Mapped[str] = mapped_column(String, index=True)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     system_prompt: Mapped[str] = mapped_column(Text)
#     greeting: Mapped[str] = mapped_column(String)
#     owner_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    
#     # Provider IDs
#     llm_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
#         UUID(as_uuid=True), 
#         ForeignKey("llm_providers.id"), 
#         nullable=False
#     )
#     tts_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
#         UUID(as_uuid=True), 
#         ForeignKey("tts_providers.id"), 
#         nullable=False
#     )
#     stt_provider_id: Mapped[uuid_pkg.UUID] = mapped_column(
#         UUID(as_uuid=True), 
#         ForeignKey("stt_providers.id"), 
#         nullable=False
#     )
    
#     # Configuration fields
#     llm_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
#     tts_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
#     stt_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
#     allow_interruptions: Mapped[bool] = mapped_column(Boolean, default=True)
#     profile_options: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
#     interrupt_speech_duration: Mapped[float] = mapped_column(Float, default=0.5)
#     interrupt_min_words: Mapped[int] = mapped_column(Integer, default=0)
#     min_endpointing_delay: Mapped[float] = mapped_column(Float, default=0.5)
#     max_endpointing_delay: Mapped[float] = mapped_column(Float, default=6.0)
#     max_nested_function_calls: Mapped[int] = mapped_column(Integer, default=1)
#     active: Mapped[bool] = mapped_column(Boolean, default=True)
#     is_default: Mapped[bool] = mapped_column(Boolean, default=False)
#     knowledge_bases_data: Mapped[list] = mapped_column(JSONB, default_factory=list)

#     # Timestamps
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
    
#     # Relationships
#     agent_profile = relationship("AgentProfile", foreign_keys=[agent_id])
#     owner = relationship("User", foreign_keys=[owner_id])
#     llm_provider = relationship("LLMProvider", foreign_keys=[llm_provider_id])
#     tts_provider = relationship("TTSProvider", foreign_keys=[tts_provider_id])
#     stt_provider = relationship("STTProvider", foreign_keys=[stt_provider_id])