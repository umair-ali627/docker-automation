# # app/api/v1/agent_profiles.py
# from typing import List, Optional, Dict, Any
# import uuid
# from fastapi import APIRouter, Depends, HTTPException, Query, Body
# from sqlalchemy.ext.asyncio import AsyncSession

# from ...schemas.agent_profile import (
#     AgentProfile, 
#     AgentProfileCreate, 
#     AgentProfileUpdate, 
#     AgentProfileList,
#     OpenAILLMOptions,
#     GoogleLLMOptions,
#     OpenAITTSOptions,
#     GoogleTTSOptions,
#     DeepgramSTTOptions,
#     GoogleSTTOptions,
#     AgentProfileInDB
# )
# from ...schemas.provider_types import LLMProvider, TTSProvider, STTProvider
# from ...core.db.database import async_get_db
# from ...crud.crud_agent_profiles import crud_agent_profiles
# from ...api.dependencies import get_current_user
# from ...models.user import User

# router = APIRouter(tags=["agent-profile"])


# @router.get("/agent-profile", response_model=AgentProfileList)
# async def list_agent_profiles(
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
#     skip: int = 0,
#     limit: int = 100,
#     show_all: bool = False,
# ):
#     """
#     List agent profiles.
    
#     Regular users can only see their own profiles.
#     Superusers can see all profiles or filter by owner_id.
#     """
#     owner_id = None
#     if not current_user["is_superuser"] or not show_all:
#         owner_id = current_user["id"]
    
#     profiles = await crud_agent_profiles.get_multi(
#         db, skip=skip, limit=limit, owner_id=owner_id
#     )
#     return {
#         "items": profiles,
#         "total": len(profiles)
#     }


# @router.post("/agent-profile", response_model=AgentProfile)
# async def create_agent_profile(
#     profile_in: AgentProfileCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Create a new agent profile.
#     """

#     profile = await crud_agent_profiles.create(
#         db, obj_in=profile_in, owner_id=current_user["id"]
#     )
#     return profile


# @router.get("/agent-profile/{profile_id}", response_model=AgentProfile)
# async def get_agent_profile(
#     profile_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Get an agent profile by ID.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to access this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     return profile


# @router.put("/agent-profile/{profile_id}", response_model=dict)
# async def update_agent_profile(
#     profile_id: uuid.UUID,
#     profile_in: AgentProfileUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Update an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to update this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     owner_id = current_user["id"] if not current_user["is_superuser"] else None
#     updated_profile = await crud_agent_profiles.update(
#         db=db, id=profile_id, obj_in=profile_in, owner_id=owner_id
#     )
#     return {"success": True, "message": "Agent Profile updated successfully"}


# @router.delete("/agent-profile/{profile_id}", response_model=AgentProfile)
# async def delete_agent_profile(
#     profile_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Delete an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to delete this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     deleted_profile = await crud_agent_profiles.delete(db=db, id=profile_id)
#     return deleted_profile


# @router.get("/agent-profile/by-name/{profile_name}", response_model=AgentProfile)
# async def get_profile_by_name(
#     profile_name: str,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Get an agent profile by name.
#     """
#     profile = await crud_agent_profiles.get_by_name(db=db, name=profile_name)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to access this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     return profile


# # Added endpoints for provider-specific options

# @router.get("/agent-profile-provider-options", response_model=Dict[str, Dict[str, Dict[str, Any]]])
# async def get_provider_options():
#     """
#     Get available options schemas for all providers.
#     Returns a nested dictionary of provider types and their available options.
#     """
#     provider_options = {
#         "llm": {
#             LLMProvider.OPENAI: OpenAILLMOptions().model_dump(),
#             LLMProvider.GOOGLE: GoogleLLMOptions().model_dump(),
#         },
#         "tts": {
#             TTSProvider.OPENAI: OpenAITTSOptions().model_dump(),
#             TTSProvider.GOOGLE: GoogleTTSOptions().model_dump(),
#         },
#         "stt": {
#             STTProvider.DEEPGRAM: DeepgramSTTOptions().model_dump(),
#             STTProvider.GOOGLE: GoogleSTTOptions().model_dump(),
#         }
#     }
#     return provider_options


# @router.post("/agent-profile/{profile_id}/llm-options", response_model=AgentProfile)
# async def update_llm_options(
#     profile_id: uuid.UUID,
#     options: Dict[str, Any] = Body(...),
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Update LLM options for an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check permissions
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # Create update object with just the LLM options
#     update_obj = AgentProfileUpdate(llm_options=options)
    
#     # Update the profile
#     updated_profile = await crud_agent_profiles.update(
#         db=db, id=profile_id, obj_in=update_obj, owner_id=current_user["id"]
#     )
    
#     return updated_profile


# @router.post("/agent-profile/{profile_id}/tts-options", response_model=AgentProfile)
# async def update_tts_options(
#     profile_id: uuid.UUID,
#     options: Dict[str, Any] = Body(...),
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Update TTS options for an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check permissions
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # Create update object with just the TTS options
#     update_obj = AgentProfileUpdate(tts_options=options)
    
#     # Update the profile
#     updated_profile = await crud_agent_profiles.update(
#         db=db, id=profile_id, obj_in=update_obj, owner_id=current_user["id"]
#     )
    
#     return updated_profile


# @router.post("/agent-profile/{profile_id}/stt-options", response_model=AgentProfile)
# async def update_stt_options(
#     profile_id: uuid.UUID,
#     options: Dict[str, Any] = Body(...),
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Update STT options for an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check permissions
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # Create update object with just the STT options
#     update_obj = AgentProfileUpdate(stt_options=options)
    
#     # Update the profile
#     updated_profile = await crud_agent_profiles.update(
#         db=db, id=profile_id, obj_in=update_obj, owner_id=current_user["id"]
#     )
    
#     return updated_profile


# from typing import List
# import uuid
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.ext.asyncio import AsyncSession

# from ...schemas.agent_profile import (
#     AgentProfile,
#     AgentProfileCreate,
#     AgentProfileUpdate,
#     AgentProfileList,
# )
# from ...core.db.database import async_get_db
# from ...crud.crud_agent_profiles import crud_agent_profiles
# from ...api.dependencies import get_current_user
# from ...models.user import User

# router = APIRouter(tags=["agent-profile"])

# @router.get("/agent-profile", response_model=AgentProfileList)
# async def list_agent_profiles(
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
#     skip: int = 0,
#     limit: int = 100,
#     show_all: bool = Query(False, description="Show all profiles (superusers only)"),
# ):
#     """
#     List agent profiles.
    
#     Regular users can only see their own profiles.
#     Superusers can see all profiles or filter by owner_id.
#     """
#     owner_id = None
#     if not current_user["is_superuser"] or not show_all:
#         owner_id = current_user["id"]
    
#     profiles = await crud_agent_profiles.get_multi(
#         db, skip=skip, limit=limit, owner_id=owner_id
#     )
#     return {
#         "items": profiles,
#         "total": len(profiles)
#     }

# @router.post("/agent-profile", response_model=AgentProfile)
# async def create_agent_profile(
#     profile_in: AgentProfileCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Create a new agent profile.
#     """
#     profile = await crud_agent_profiles.create(
#         db, obj_in=profile_in, owner_id=current_user["id"]
#     )
#     return profile

# @router.get("/agent-profile/{profile_id}", response_model=AgentProfile)
# async def get_agent_profile(
#     profile_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Get an agent profile by ID.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to access this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     return profile

# @router.put("/agent-profile/{profile_id}", response_model=dict)
# async def update_agent_profile(
#     profile_id: uuid.UUID,
#     profile_in: AgentProfileUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Update an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to update this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     owner_id = current_user["id"] if not current_user["is_superuser"] else None
#     updated_profile = await crud_agent_profiles.update(
#         db=db, id=profile_id, obj_in=profile_in, owner_id=owner_id
#     )
#     return {"success": True, "message": "Agent Profile updated successfully"}

# @router.delete("/agent-profile/{profile_id}", response_model=AgentProfile)
# async def delete_agent_profile(
#     profile_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Delete an agent profile.
#     """
#     profile = await crud_agent_profiles.get(db=db, id=profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to delete this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     deleted_profile = await crud_agent_profiles.delete(db=db, id=profile_id)
#     return deleted_profile

# @router.get("/agent-profile/by-name/{profile_name}", response_model=AgentProfile)
# async def get_profile_by_name(
#     profile_name: str,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Get an agent profile by name.
#     """
#     profile = await crud_agent_profiles.get_by_name(db=db, name=profile_name)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Agent profile not found")
    
#     # Check if the user has permission to access this profile
#     if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     return profile

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from ...services.sip_factory import sip_factory # Adjust this import path

from ...schemas.agent_profile import (
    AgentProfile,
    AgentProfileCreate,
    AgentProfileInDB,
    AgentProfileUpdate,
    AgentProfileList,
)
from ...core.db.database import async_get_db
from ...crud.crud_agent_profiles import crud_agent_profiles
from ...api.dependencies import get_current_user
from ...models.user import User
from ...models import AgentProfile

router = APIRouter(tags=["agent-profile"])

@router.get("/agent-profile", response_model=AgentProfileList)
async def list_agent_profiles(
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    show_all: bool = Query(False, description="Show all profiles (superusers only)"),
):
    """
    List agent profiles.
    
    Regular users can only see their own profiles.
    Superusers can see all profiles or filter by owner_id.
    """
    owner_id = None
    if not current_user["is_superuser"] or not show_all:
        owner_id = current_user["id"]
    
    profiles = await crud_agent_profiles.get_multi(
        db, skip=skip, limit=limit, owner_id=owner_id
    )
    return {
        "items": profiles,
        "total": len(profiles)
    }

@router.post("/agent-profile", response_model=AgentProfileInDB)
async def create_agent_profile(
    profile_in: AgentProfileCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new agent profile.
    """
    profile = await crud_agent_profiles.create(
        db, obj_in=profile_in, owner_id=current_user["id"]
    )
    return profile

@router.get("/agent-profile/{profile_id}", response_model=AgentProfileInDB)
async def get_agent_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get an agent profile by ID.
    """
    profile = await crud_agent_profiles.get(db=db, id=profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return profile

@router.put("/agent-profile/{profile_id}", response_model=AgentProfileInDB)
async def update_agent_profile(
    profile_id: uuid.UUID,
    profile_in: AgentProfileUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update an agent profile.
    """
    owner_id = current_user["id"] if not current_user["is_superuser"] else None
    updated_profile = await crud_agent_profiles.update(
        db=db, id=profile_id, obj_in=profile_in, owner_id=owner_id
    )
    return updated_profile

@router.delete("/agent-profile/{agent_profile_id}", response_model=Optional[AgentProfileInDB])
async def delete_agent_profile(
    agent_profile_id: uuid.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an agent profile.
    """
    profile = await crud_agent_profiles.get(db=db, id=agent_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    deleted_profile = await crud_agent_profiles.delete(db=db, id=agent_profile_id)
    return deleted_profile

@router.get("/agent-profile/by-name/{profile_name}", response_model=AgentProfileInDB)
async def get_profile_by_name(
    profile_name: str,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get an agent profile by name.
    """
    profile = await crud_agent_profiles.get_by_name(db=db, name=profile_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    if not current_user["is_superuser"] and profile.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return profile
