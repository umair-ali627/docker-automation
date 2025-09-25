# from pydantic import BaseModel, UUID4
# from typing import List, Dict, Any, Optional
# from datetime import datetime

# # Base for all
# class ProviderResponse(BaseModel):
#     message: str
#     data: Any
#     error: Optional[str] = None
#     success: bool = True

# # LLM
# class LLMProviderBase(BaseModel):
#     provider: str
#     models: List[str]

# class LLMProviderCreate(LLMProviderBase):
#     pass

# class LLMProviderUpdate(BaseModel):
#     provider: Optional[str] = None
#     models: Optional[List[str]] = None

# class LLMProviderInDB(LLMProviderBase):
#     id: UUID4
#     created_at: Optional[datetime] = None
#     updated_at: Optional[datetime] = None

# # TTS
# class TTSModel(BaseModel):
#     model: str
#     languages: List[str]

# class TTSVoice(BaseModel):
#     id: str
#     age: str
#     name: str
#     accent: str
#     gender: str
#     voice_url: Optional[str] = None

# class TTSProviderBase(BaseModel):
#     provider: str
#     models: List[TTSModel]
#     voices: List[TTSVoice]

# class TTSProviderCreate(TTSProviderBase):
#     pass

# class TTSProviderUpdate(BaseModel):
#     provider: Optional[str] = None
#     models: Optional[List[TTSModel]] = None
#     voices: Optional[List[TTSVoice]] = None

# class TTSProviderInDB(TTSProviderBase):
#     id: UUID4
#     created_at: Optional[datetime] = None
#     updated_at: Optional[datetime] = None

# # STT
# class STTModel(BaseModel):
#     model: str
#     languages: List[str]

# class STTProviderBase(BaseModel):
#     provider: str
#     models: List[STTModel]

# class STTProviderCreate(STTProviderBase):
#     pass

# class STTProviderUpdate(BaseModel):
#     provider: Optional[str] = None
#     models: Optional[List[STTModel]] = None

# class STTProviderInDB(STTProviderBase):
#     id: UUID4
#     created_at: Optional[datetime] = None
#     updated_at: Optional[datetime] = None


from pydantic import BaseModel, UUID4
from typing import List, Dict, Any, Optional
from datetime import datetime

# Base response model
class ProviderResponse(BaseModel):
    message: str
    data: Any
    error: Optional[str] = None
    success: bool = True

    model_config = {
        "from_attributes": True  # Enable ORM compatibility
    }

# LLM
class LLMProviderBase(BaseModel):
    provider: str
    models: List[str]

    model_config = {
        "from_attributes": True
    }

class LLMProviderCreate(LLMProviderBase):
    pass

class LLMProviderUpdate(BaseModel):
    provider: Optional[str] = None
    models: Optional[List[str]] = None

    model_config = {
        "from_attributes": True
    }

class LLMProviderInDB(LLMProviderBase):
    id: UUID4
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True  # Enable ORM compatibility
    }

# TTS
class TTSModel(BaseModel):
    model: str
    languages: List[str]

    model_config = {
        "from_attributes": True
    }

class TTSVoice(BaseModel):
    id: str
    age: str
    name: str
    accent: str
    gender: str
    voice_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class TTSProviderBase(BaseModel):
    provider: str
    models: List[TTSModel]
    voices: List[TTSVoice]

    model_config = {
        "from_attributes": True
    }

class TTSProviderCreate(TTSProviderBase):
    pass

class TTSProviderUpdate(BaseModel):
    provider: Optional[str] = None
    models: Optional[List[TTSModel]] = None
    voices: Optional[List[TTSVoice]] = None

    model_config = {
        "from_attributes": True
    }

class TTSProviderInDB(TTSProviderBase):
    id: UUID4
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True  # Enable ORM compatibility
    }

# STT
class STTModel(BaseModel):
    model: str
    languages: List[str]

    model_config = {
        "from_attributes": True
    }

class STTProviderBase(BaseModel):
    provider: str
    models: List[STTModel]

    model_config = {
        "from_attributes": True
    }

class STTProviderCreate(STTProviderBase):
    pass

class STTProviderUpdate(BaseModel):
    provider: Optional[str] = None
    models: Optional[List[STTModel]] = None

    model_config = {
        "from_attributes": True
    }

class STTProviderInDB(STTProviderBase):
    id: UUID4
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True  # Enable ORM compatibility
    }
    
    