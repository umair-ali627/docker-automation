from pydantic import BaseModel, Field, ConfigDict, UUID4, field_validator
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from ..schemas.agent_profile import ProfileOptions, ProviderBase, STTOptions, TTSOptions

from ..schemas.document import KnowledgeBaseWithDocsRead


class ConnectionBase(BaseModel):
    """Base schema for connections"""
    room_id: str
    agent_id: UUID4
    call_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    system_prompt: str
    greeting: str
    owner_id: uuid.UUID
    llm_provider: ProviderBase
    tts_provider: ProviderBase
    stt_provider: ProviderBase
    llm_options: Dict[str, Any] = Field(default_factory=dict)
    # CHANGED: Use the typed Pydantic models for options
    tts_options: TTSOptions = Field(default_factory=TTSOptions)
    stt_options: STTOptions = Field(default_factory=STTOptions)
    profile_options: Dict[str, Any] = Field(default_factory=lambda: ProfileOptions().model_dump())
    allow_interruptions: bool = Field(default=True)
    interrupt_speech_duration: float = Field(default=0.5)
    interrupt_min_words: int = Field(default=0)
    min_endpointing_delay: float = 0.5
    max_endpointing_delay: float = 6.0
    active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    is_record: bool = Field(default=False)
    max_nested_function_calls: int = Field(default=1)
    model_config = ConfigDict(from_attributes=True)

# This is the new schema for the connections endpoint
class ConnectionCreateSimple(BaseModel):
    """Schema for creating a connection with just the room and agent IDs."""
    room_id: str
    agent_id: UUID4
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class ConnectionCreate(BaseModel):
    """Schema for creating a connection"""
    room_id: str
    agent_id: UUID4
    name: str
    description: Optional[str] = None
    system_prompt: str
    greeting: str
    llm_provider: ProviderBase
    tts_provider: ProviderBase
    stt_provider: ProviderBase
    llm_options: Dict[str, Any] = Field(default_factory=dict)
    # CHANGED: Use the typed Pydantic models here as well for consistent API input
    tts_options: TTSOptions = Field(default_factory=TTSOptions)
    stt_options: STTOptions = Field(default_factory=STTOptions)
    
    profile_options: Dict[str, Any] = Field(default_factory=lambda: ProfileOptions().model_dump())
    allow_interruptions: bool = Field(default=True)
    interrupt_speech_duration: float = Field(default=0.5)
    interrupt_min_words: int = Field(default=0)
    min_endpointing_delay: float = 0.5
    max_endpointing_delay: float = 6.0
    active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    is_record: bool = Field(default=False)
    max_nested_function_calls: int = Field(default=1)
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class ConnectionCreateInternal(BaseModel):
    """Schema for internal creation of connection"""
    room_id: str
    agent_id: UUID4
    call_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    system_prompt: str
    greeting: str
    owner_id: uuid.UUID
    llm_provider_id: UUID4
    tts_provider_id: UUID4
    stt_provider_id: UUID4
    llm_options: Dict[str, Any] = {}
    tts_options: Dict[str, Any] = {}
    stt_options: Dict[str, Any] = {}
    profile_options: Dict[str, Any] = {"background_audio": {"enabled": False, "audio_path": "office-ambience.mp3", "volume": 0.3, "loop": True}}
    allow_interruptions: bool = True
    interrupt_speech_duration: float = 0.5
    interrupt_min_words: int = 0
    min_endpointing_delay: float = 0.5
    max_endpointing_delay: float = 6.0
    active: bool = True
    is_default: bool = False
    is_record: bool = False  # <-- Field added
    max_nested_function_calls: int = 1
    # Add this new field
    knowledge_bases_data: List[dict] = [] 
    model_config = ConfigDict(from_attributes=True)

class ConnectionInDB(ConnectionBase):
    """Schema for connection in database"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # knowledge_bases: List[KnowledgeBaseWithDocsRead] = [] # Change this line
    knowledge_bases: List[KnowledgeBaseWithDocsRead] = Field(alias="knowledge_bases_data", default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class Connection(ConnectionInDB):
    """Schema for connection returned to API"""
    pass
