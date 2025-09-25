from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...services.voice import voice_service
from ..dependencies import get_current_user
from ...models.user import User

router = APIRouter(tags=["voices"])

# Define schema models for the API
class VoiceResponse(BaseModel):
    id: str
    provider: str
    providerId: str
    name: str
    description: Optional[str] = None
    slug: str

class VoicesListResponse(BaseModel):
    items: List[VoiceResponse]
    total: int

@router.get("/voices", response_model=VoicesListResponse)
async def list_voices(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List available voice options.
    
    Args:
        provider: Optional provider filter (e.g., 'openai', 'cartesia')
    """
    if provider:
        voices_data = voice_service.get_voices_by_provider(provider)
    else:
        voices_data = voice_service.get_all_voices()
    
    # Convert to the response format
    voices = [
        VoiceResponse(
            id=voice.get('id'),
            provider=voice.get('provider'),
            providerId=voice.get('providerId'),
            name=voice.get('name'),
            description=voice.get('description', ''),
            slug=voice.get('slug')
        )
        for voice in voices_data
    ]
    
    return {
        "items": voices,
        "total": len(voices)
    }

@router.get("/voices/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get details for a specific voice by ID.
    """
    voice = voice_service.get_voice_by_id(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return VoiceResponse(
        id=voice.get('id'),
        provider=voice.get('provider'),
        providerId=voice.get('providerId'),
        name=voice.get('name'),
        description=voice.get('description', ''),
        slug=voice.get('slug')
    )

@router.get("/providers", response_model=List[str])
async def list_providers(
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of all available voice providers.
    """
    return voice_service.get_providers()