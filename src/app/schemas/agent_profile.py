# from pydantic import BaseModel, Field, UUID4, ConfigDict, validator
# from typing import Optional, List, Dict, Any
# import uuid
# from enum import Enum

# from .provider_types import LLMProvider, TTSProvider, STTProvider

# # Provider-specific option schemas
# class OpenAILLMOptions(BaseModel):
#     model: str = "gpt-4o"
#     temperature: float = 0.7

# class GoogleLLMOptions(BaseModel):
#     model: str = "gemini-pro"
#     temperature: float = 0.7

# class OpenAITTSOptions(BaseModel):
#     voice: str = "alloy"
#     speed: float = 1.0

# class GoogleTTSOptions(BaseModel):
#     voice: str = "en-US-Neural2-F"
#     speaking_rate: float = 1.0
#     pitch: float = 0.0

# class DeepgramSTTOptions(BaseModel):
#     model: str = "nova-3-general"
#     model_telephony: str = "nova-2-phonecall"

# class GoogleSTTOptions(BaseModel):
#     model: str = "latest"
#     language_code: str = "en-US"

# # Default profile options for background audio
# class BackgroundAudioOptions(BaseModel):
#     enabled: bool = False
#     audio_path: str = "office-ambience.mp3"
#     volume: float = 0.3
#     loop: bool = True


# class ProfileOptions(BaseModel):
#     background_audio: BackgroundAudioOptions = Field(default_factory=BackgroundAudioOptions)
#     # custom_features: Dict[str, Any] = Field(default_factory=dict)

# class AgentProfileBase(BaseModel):
#     name: str
#     description: Optional[str] = None
#     system_prompt: str = Field(
#         default="You are a voice assistant created by LiveKit. Your interface with users will be voice. "
#                "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
#     )
#     greeting: str = Field(default="Hey, how can I help you today?")
    
#     # Provider selections
#     llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
#     tts_provider: TTSProvider = Field(default=TTSProvider.OPENAI)
#     stt_provider: STTProvider = Field(default=STTProvider.DEEPGRAM)
    
#     # Provider options
#     llm_options: Dict[str, Any] = Field(default_factory=lambda: OpenAILLMOptions().model_dump())
#     tts_options: Dict[str, Any] = Field(default_factory=lambda: OpenAITTSOptions().model_dump())
#     stt_options: Dict[str, Any] = Field(default_factory=lambda: DeepgramSTTOptions().model_dump())
    
#     # Behavioral settings
#     profile_options: Dict[str, Any] = Field(default_factory=lambda: ProfileOptions().model_dump())
#     allow_interruptions: bool = Field(default=True)
#     interrupt_speech_duration: float = Field(default=0.5)
#     interrupt_min_words: int = Field(default=0)
#     min_endpointing_delay: float = Field(default=0.5)
#     max_endpointing_delay: float = Field(default=6.0)
#     active: bool = Field(default=True)
#     is_default: bool = Field(default=False)
#     max_nested_function_calls: int = Field(default=1)
#     # Validators to ensure options match the selected provider
#     @validator('llm_options')
#     def validate_llm_options(cls, v, values):
#         provider = values.get('llm_provider')
#         if provider == LLMProvider.OPENAI:
#             OpenAILLMOptions(**v)
#         elif provider == LLMProvider.GOOGLE:
#             GoogleLLMOptions(**v)
#         return v
    
#     @validator('tts_options')
#     def validate_tts_options(cls, v, values):
#         provider = values.get('tts_provider')
#         if provider == TTSProvider.OPENAI:
#             OpenAITTSOptions(**v)
#         elif provider == TTSProvider.GOOGLE:
#             GoogleTTSOptions(**v)
#         return v
    
#     @validator('stt_options')
#     def validate_stt_options(cls, v, values):
#         provider = values.get('stt_provider')
#         if provider == STTProvider.DEEPGRAM:
#             DeepgramSTTOptions(**v)
#         elif provider == STTProvider.GOOGLE:
#             GoogleSTTOptions(**v)
#         return v
    
#     @validator('profile_options')
#     def validate_profile_options(cls, v):
#         # Basic validation - could be expanded based on needs
#         if 'background_audio' in v:
#             BackgroundAudioOptions(**v['background_audio'])
#         return v

# class AgentProfileCreate(AgentProfileBase):
#     """Schema for creating an agent profile"""
#     model_config = ConfigDict(extra="forbid")

# class AgentProfileCreateInternal(AgentProfileCreate):
#     """Schema for internal creation of agent profile (including owner_id)"""
#     owner_id: uuid.UUID

# class AgentProfileUpdateInternal(AgentProfileBase):
#     """Schema for internal updates to agent profile (all fields required)"""
#     pass

# class AgentProfileUpdate(BaseModel):
#     """Schema for external updates to agent profile (all fields optional)"""
#     model_config = ConfigDict(extra="forbid")
    
#     name: Optional[str] = None
#     description: Optional[str] = None
#     system_prompt: Optional[str] = None
#     greeting: Optional[str] = None
    
#     # Provider selections
#     llm_provider: Optional[LLMProvider] = None
#     tts_provider: Optional[TTSProvider] = None
#     stt_provider: Optional[STTProvider] = None
    
#     # Provider options
#     llm_options: Optional[Dict[str, Any]] = None
#     tts_options: Optional[Dict[str, Any]] = None
#     stt_options: Optional[Dict[str, Any]] = None
    
#     # Behavioral settings
#     profile_options: Optional[Dict[str, Any]] = None
#     allow_interruptions: Optional[bool] = None
#     interrupt_speech_duration: Optional[float] = None
#     interrupt_min_words: Optional[int] = None
#     min_endpointing_delay: Optional[float] = None
#     max_endpointing_delay: Optional[float] = None
#     active: Optional[bool] = None
#     is_default: Optional[bool] = None
#     max_nested_function_calls: Optional[int] = None

# class AgentProfileDelete(BaseModel):
#     """Schema for deleting an agent profile"""
#     model_config = ConfigDict(extra="forbid")
#     id: UUID4

# class AgentProfileInDB(AgentProfileBase):
#     """Schema for agent profile in database"""
#     id: UUID4
#     owner_id: uuid.UUID
    
#     model_config = ConfigDict(from_attributes=True)

# class AgentProfile(AgentProfileInDB):
#     """Schema for agent profile returned to API"""
#     pass

# class AgentProfileList(BaseModel):
#     """Schema for a list of agent profiles"""
#     items: List[AgentProfile]
#     total: int


from pydantic import BaseModel, Field, ConfigDict, UUID4, field_validator
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

# --- Helper Models for Options ---

class TTSOptions(BaseModel):
    # ADDED: Typed model for TTS Options
    model: Optional[str] = None
    voice: Optional[str] = None
    speed: float = 1.0
    language: Optional[str] = 'en'  # ADDED: Language field with a default

class STTOptions(BaseModel):
    # ADDED: Typed model for STT Options
    model: Optional[str] = None
    model_telephony: Optional[str] = None
    language: Optional[str] = 'en'  # ADDED: Language field with a default


class BackgroundAudioOptions(BaseModel):
    enabled: bool = False
    audio_path: str = "office-ambience.mp3"
    volume: float = 0.3
    loop: bool = True
    model_config = ConfigDict(from_attributes=True)

class ProfileOptions(BaseModel):
    background_audio: BackgroundAudioOptions = Field(default_factory=BackgroundAudioOptions)
    model_config = ConfigDict(from_attributes=True)
    
class ProviderBase(BaseModel):
    id: Optional[UUID4] = None
    provider: str

    @field_validator("id", mode="before")
    def handle_empty_id(cls, value):
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    model_config = ConfigDict(from_attributes=True)

class AgentProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str = Field(
        default="You are a voice assistant created by LiveKit. Your interface with users will be voice. "
                "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
    )
    greeting: str = Field(default="Hey, how can I help you today?")
    
    llm_provider: ProviderBase
    tts_provider: ProviderBase
    stt_provider: ProviderBase
    
    # CHANGED: Use typed models instead of Dict
    llm_options: Dict[str, Any] = Field(default_factory=dict)
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
    is_record: bool = Field(default=False, description="Enable or disable conversation recording.")
    is_deleted: bool = Field(default=False)
    max_nested_function_calls: int = Field(default=1)

    model_config = ConfigDict(from_attributes=True)

class AgentProfileCreate(AgentProfileBase):
    """Schema for creating an agent profile"""
    # At creation, ensure options are dumped to dict for internal model
    @field_validator('tts_options', 'stt_options', mode='before')
    def options_to_dict(cls, v):
        if isinstance(v, BaseModel):
            return v.model_dump()
        return v
        
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class AgentProfileCreateInternal(BaseModel):
    """Schema for internal creation of agent profile (including owner_id)"""
    name: str
    description: Optional[str] = None
    system_prompt: str
    greeting: str
    llm_provider_id: UUID4
    tts_provider_id: UUID4
    stt_provider_id: UUID4
    # CHANGED: These remain dicts for database compatibility
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
    is_record: bool = False
    is_deleted: bool = False
    max_nested_function_calls: int = 1
    owner_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class AgentProfileUpdateInternal(BaseModel):
    """Schema for internal updates to agent profile (all fields optional)"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    greeting: Optional[str] = None
    llm_provider_id: Optional[UUID4] = None
    tts_provider_id: Optional[UUID4] = None
    stt_provider_id: Optional[UUID4] = None
    # CHANGED: These remain dicts for database compatibility
    llm_options: Optional[Dict[str, Any]] = None
    tts_options: Optional[Dict[str, Any]] = None
    stt_options: Optional[Dict[str, Any]] = None
    profile_options: Optional[Dict[str, Any]] = None
    allow_interruptions: Optional[bool] = None
    interrupt_speech_duration: Optional[float] = None
    interrupt_min_words: Optional[int] = None
    min_endpointing_delay: Optional[float] = None
    max_endpointing_delay: Optional[float] = None
    active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_record: Optional[bool] = None
    is_deleted: Optional[bool] = None
    max_nested_function_calls: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class AgentProfileUpdate(BaseModel):
    """Schema for external updates to agent profile (all fields optional)"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    greeting: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    llm_provider: Optional[ProviderBase] = None
    tts_provider: Optional[ProviderBase] = None
    stt_provider: Optional[ProviderBase] = None
    # CHANGED: Use typed models for updates as well
    llm_options: Optional[Dict[str, Any]] = None
    tts_options: Optional[TTSOptions] = None
    stt_options: Optional[STTOptions] = None
    profile_options: Optional[Dict[str, Any]] = None
    allow_interruptions: Optional[bool] = None
    interrupt_speech_duration: Optional[float] = None
    interrupt_min_words: Optional[int] = None
    min_endpointing_delay: Optional[float] = None
    max_endpointing_delay: Optional[float] = None
    active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_record: Optional[bool] = None
    max_nested_function_calls: Optional[int] = None
    
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class AgentProfileDelete(BaseModel):
    id: UUID4
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class AgentProfileInDB(AgentProfileBase):
    id: UUID4
    owner_id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class AgentProfile(AgentProfileInDB):
    pass

class AgentProfileList(BaseModel):
    items: List[AgentProfileInDB]
    total: int
    model_config = ConfigDict(from_attributes=True)