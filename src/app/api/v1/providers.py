# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List
# from uuid import UUID

# from ...core.db.database import async_get_db
# from ...api.dependencies import get_current_user
# from ...models.user import User
# from ...crud.crud_providers import (
#     get_llm_providers, get_llm_provider, create_llm_provider, update_llm_provider, delete_llm_provider,
#     get_tts_providers, get_tts_provider, create_tts_provider, update_tts_provider, delete_tts_provider,
#     get_stt_providers, get_stt_provider, create_stt_provider, update_stt_provider, delete_stt_provider
# )
# from ...schemas.providers import (
#     LLMProviderCreate, LLMProviderUpdate, LLMProviderInDB,
#     TTSProviderCreate, TTSProviderUpdate, TTSProviderInDB,
#     STTProviderCreate, STTProviderUpdate, STTProviderInDB,
#     ProviderResponse
# )

# router = APIRouter(tags=["providers"])
# print("Providers router loaded successfully")  # Debug

# # LLM Endpoints
# @router.get("/providers/llm", response_model=ProviderResponse)
# async def list_llm_providers(db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     providers = await get_llm_providers(db)
#     return ProviderResponse(message="LLM providers retrieved successfully", data=[LLMProviderInDB.from_orm(p) for p in providers])

# @router.post("/providers/llm", response_model=ProviderResponse)
# async def create_llm_provider_endpoint(obj_in: LLMProviderCreate, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await create_llm_provider(db, obj_in)
#     return ProviderResponse(message="LLM provider created successfully", data=LLMProviderInDB.from_orm(provider))

# @router.get("/providers/llm/{id}", response_model=ProviderResponse)
# async def get_llm_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await get_llm_provider(db, id)
#     if not provider:
#         raise HTTPException(status_code=404, detail="LLM provider not found")
#     return ProviderResponse(message="LLM provider retrieved successfully", data=LLMProviderInDB.from_orm(provider))

# @router.put("/providers/llm/{id}", response_model=ProviderResponse)
# async def update_llm_provider_endpoint(id: UUID, obj_in: LLMProviderUpdate, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await update_llm_provider(db, id, obj_in)
#     if not provider:
#         raise HTTPException(status_code=404, detail="LLM provider not found")
#     return ProviderResponse(message="LLM provider updated successfully", data=LLMProviderInDB.from_orm(provider))

# @router.delete("/providers/llm/{id}", response_model=ProviderResponse)
# async def delete_llm_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     success = await delete_llm_provider(db, id)
#     if not success:
#         raise HTTPException(status_code=404, detail="LLM provider not found")
#     return ProviderResponse(message="LLM provider deleted successfully", data=None, success=True)

# # TTS Endpoints
# @router.get("/providers/tts", response_model=ProviderResponse)
# async def list_tts_providers(db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     providers = await get_tts_providers(db)
#     return ProviderResponse(message="TTS providers retrieved successfully", data=[TTSProviderInDB.from_orm(p) for p in providers])

# @router.post("/providers/tts", response_model=ProviderResponse)
# async def create_tts_provider_endpoint(obj_in: TTSProviderCreate, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await create_tts_provider(db, obj_in)
#     return ProviderResponse(message="TTS provider created successfully", data=TTSProviderInDB.from_orm(provider))

# @router.get("/providers/tts/{id}", response_model=ProviderResponse)
# async def get_tts_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await get_tts_provider(db, id)
#     if not provider:
#         raise HTTPException(status_code=404, detail="TTS provider not found")
#     return ProviderResponse(message="TTS provider retrieved successfully", data=TTSProviderInDB.from_orm(provider))

# @router.put("/providers/tts/{id}", response_model=ProviderResponse)
# async def update_tts_provider_endpoint(id: UUID, obj_in: TTSProviderUpdate, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await update_tts_provider(db, id, obj_in)
#     if not provider:
#         raise HTTPException(status_code=404, detail="TTS provider not found")
#     return ProviderResponse(message="TTS provider updated successfully", data=TTSProviderInDB.from_orm(provider))

# @router.delete("/providers/tts/{id}", response_model=ProviderResponse)
# async def delete_tts_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     success = await delete_tts_provider(db, id)
#     if not success:
#         raise HTTPException(status_code=404, detail="TTS provider not found")
#     return ProviderResponse(message="TTS provider deleted successfully", data=None, success=True)

# # STT Endpoints
# @router.get("/providers/stt", response_model=ProviderResponse)
# async def list_stt_providers(db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     providers = await get_stt_providers(db)
#     return ProviderResponse(message="STT providers retrieved successfully", data=[STTProviderInDB.from_orm(p) for p in providers])

# @router.post("/providers/stt", response_model=ProviderResponse)
# async def create_stt_provider_endpoint(obj_in: STTProviderCreate, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await create_stt_provider(db, obj_in)
#     return ProviderResponse(message="STT provider created successfully", data=STTProviderInDB.from_orm(provider))

# @router.get("/providers/stt/{id}", response_model=ProviderResponse)
# async def get_stt_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await get_stt_provider(db, id)
#     if not provider:
#         raise HTTPException(status_code=404, detail="STT provider not found")
#     return ProviderResponse(message="STT provider retrieved successfully", data=STTProviderInDB.from_orm(provider))

# @router.put("/providers/stt/{id}", response_model=ProviderResponse)
# async def update_stt_provider_endpoint(id: UUID, obj_in: STTProviderUpdate, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     provider = await update_stt_provider(db, id, obj_in)
#     if not provider:
#         raise HTTPException(status_code=404, detail="STT provider not found")
#     return ProviderResponse(message="STT provider updated successfully", data=STTProviderInDB.from_orm(provider))

# @router.delete("/providers/stt/{id}", response_model=ProviderResponse)
# async def delete_stt_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: User = Depends(get_current_user)):
#     success = await delete_stt_provider(db, id)
#     if not success:
#         raise HTTPException(status_code=404, detail="STT provider not found")
#     return ProviderResponse(message="STT provider deleted successfully", data=None, success=True)






# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List
# from uuid import UUID

# from ...core.db.database import async_get_db
# from ...api.dependencies import get_current_user
# from ...models.user import User
# from ...crud.crud_providers import (
#     get_llm_providers, get_llm_provider, create_llm_provider, update_llm_provider, delete_llm_provider,
#     get_tts_providers, get_tts_provider, create_tts_provider, update_tts_provider, delete_tts_provider,
#     get_stt_providers, get_stt_provider, create_stt_provider, update_stt_provider, delete_stt_provider
# )
# from ...schemas.providers import (
#     LLMProviderCreate, LLMProviderUpdate, LLMProviderInDB,
#     TTSProviderCreate, TTSProviderUpdate, TTSProviderInDB,
#     STTProviderCreate, STTProviderUpdate, STTProviderInDB,
#     ProviderResponse
# )

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...models.user import User
from ...crud.crud_providers import (
    get_llm_providers, get_llm_provider, create_llm_provider, update_llm_provider, delete_llm_provider,
    get_tts_providers, get_tts_provider, create_tts_provider, update_tts_provider, delete_tts_provider,
    get_stt_providers, get_stt_provider, create_stt_provider, update_stt_provider, delete_stt_provider
)
from ...schemas.providers import (
    LLMProviderCreate, LLMProviderUpdate, LLMProviderInDB,
    TTSProviderCreate, TTSProviderUpdate, TTSProviderInDB,
    STTProviderCreate, STTProviderUpdate, STTProviderInDB,
    ProviderResponse
)

router = APIRouter(prefix="/providers", tags=["providers"])  # Add prefix back
print("Providers router loaded successfully")  # Debug

# LLM Endpoints
@router.get("/llm", response_model=ProviderResponse)
async def list_llm_providers(db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user), response: Response = None):
    providers = await get_llm_providers(db)
    print("Response content type:", response.media_type)
    return ProviderResponse(message="LLM providers retrieved successfully", data=[LLMProviderInDB.model_validate(p) for p in providers])

@router.post("/llm", response_model=ProviderResponse)
async def create_llm_provider_endpoint(obj_in: LLMProviderCreate, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await create_llm_provider(db, obj_in)
    return ProviderResponse(message="LLM provider created successfully", data=LLMProviderInDB.model_validate(provider))

@router.get("/llm/{id}", response_model=ProviderResponse)
async def get_llm_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await get_llm_provider(db, id)
    if not provider:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    return ProviderResponse(message="LLM provider retrieved successfully", data=LLMProviderInDB.model_validate(provider))

@router.put("/llm/{id}", response_model=ProviderResponse)
async def update_llm_provider_endpoint(id: UUID, obj_in: LLMProviderUpdate, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await update_llm_provider(db, id, obj_in)
    if not provider:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    return ProviderResponse(message="LLM provider updated successfully", data=LLMProviderInDB.model_validate(provider))

@router.delete("/llm/{id}", response_model=ProviderResponse)
async def delete_llm_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    success = await delete_llm_provider(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    return ProviderResponse(message="LLM provider deleted successfully", data=None, success=True)

# TTS Endpoints
@router.get("/tts", response_model=ProviderResponse)
async def list_tts_providers(db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    providers = await get_tts_providers(db)
    return ProviderResponse(message="TTS providers retrieved successfully", data=[TTSProviderInDB.model_validate(p) for p in providers])

@router.post("/tts", response_model=ProviderResponse)
async def create_tts_provider_endpoint(obj_in: TTSProviderCreate, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await create_tts_provider(db, obj_in)
    return ProviderResponse(message="TTS provider created successfully", data=TTSProviderInDB.model_validate(provider))

@router.get("/tts/{id}", response_model=ProviderResponse)
async def get_tts_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await get_tts_provider(db, id)
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")
    return ProviderResponse(message="TTS provider retrieved successfully", data=TTSProviderInDB.model_validate(provider))

@router.put("/tts/{id}", response_model=ProviderResponse)
async def update_tts_provider_endpoint(id: UUID, obj_in: TTSProviderUpdate, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await update_tts_provider(db, id, obj_in)
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")
    return ProviderResponse(message="TTS provider updated successfully", data=TTSProviderInDB.model_validate(provider))

@router.delete("/tts/{id}", response_model=ProviderResponse)
async def delete_tts_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    success = await delete_tts_provider(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="TTS provider not found")
    return ProviderResponse(message="TTS provider deleted successfully", data=None, success=True)

# STT Endpoints
@router.get("/stt", response_model=ProviderResponse)
async def list_stt_providers(db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    providers = await get_stt_providers(db)
    return ProviderResponse(message="STT providers retrieved successfully", data=[STTProviderInDB.model_validate(p) for p in providers])

@router.post("/stt", response_model=ProviderResponse)
async def create_stt_provider_endpoint(obj_in: STTProviderCreate, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await create_stt_provider(db, obj_in)
    return ProviderResponse(message="STT provider created successfully", data=STTProviderInDB.model_validate(provider))

@router.get("/stt/{id}", response_model=ProviderResponse)
async def get_stt_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await get_stt_provider(db, id)
    if not provider:
        raise HTTPException(status_code=404, detail="STT provider not found")
    return ProviderResponse(message="STT provider retrieved successfully", data=STTProviderInDB.model_validate(provider))

@router.put("/stt/{id}", response_model=ProviderResponse)
async def update_stt_provider_endpoint(id: UUID, obj_in: STTProviderUpdate, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    provider = await update_stt_provider(db, id, obj_in)
    if not provider:
        raise HTTPException(status_code=404, detail="STT provider not found")
    return ProviderResponse(message="STT provider updated successfully", data=STTProviderInDB.model_validate(provider))

@router.delete("/stt/{id}", response_model=ProviderResponse)
async def delete_stt_provider_endpoint(id: UUID, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_user)):
    success = await delete_stt_provider(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="STT provider not found")
    return ProviderResponse(message="STT provider deleted successfully", data=None, success=True)