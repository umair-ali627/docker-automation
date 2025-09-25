# # Complete crud/crud_providers.py

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy import update, delete
# from typing import List, Optional
# from uuid import UUID

# from ..models import LLMProvider, TTSProvider, STTProvider
# from ..schemas.providers import (
#     LLMProviderCreate, LLMProviderUpdate,
#     TTSProviderCreate, TTSProviderUpdate,
#     STTProviderCreate, STTProviderUpdate
# )

# # LLM CRUD
# async def get_llm_providers(db: AsyncSession) -> List[LLMProvider]:
#     result = await db.execute(select(LLMProvider))
#     return result.scalars().all()

# async def get_llm_provider(db: AsyncSession, id: UUID) -> Optional[LLMProvider]:
#     result = await db.execute(select(LLMProvider).where(LLMProvider.id == id))
#     return result.scalar_one_or_none()

# async def create_llm_provider(db: AsyncSession, obj_in: LLMProviderCreate) -> LLMProvider:
#     db_obj = LLMProvider(**obj_in.model_dump())
#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)
#     return db_obj

# async def update_llm_provider(db: AsyncSession, id: UUID, obj_in: LLMProviderUpdate) -> Optional[LLMProvider]:
#     update_data = obj_in.model_dump(exclude_unset=True)
#     if not update_data:
#         return await get_llm_provider(db, id)
#     await db.execute(update(LLMProvider).where(LLMProvider.id == id).values(**update_data))
#     await db.commit()
#     return await get_llm_provider(db, id)

# async def delete_llm_provider(db: AsyncSession, id: UUID) -> bool:
#     result = await db.execute(delete(LLMProvider).where(LLMProvider.id == id))
#     await db.commit()
#     return result.rowcount > 0

# # TTS CRUD
# async def get_tts_providers(db: AsyncSession) -> List[TTSProvider]:
#     result = await db.execute(select(TTSProvider))
#     return result.scalars().all()

# async def get_tts_provider(db: AsyncSession, id: UUID) -> Optional[TTSProvider]:
#     result = await db.execute(select(TTSProvider).where(TTSProvider.id == id))
#     return result.scalar_one_or_none()

# async def create_tts_provider(db: AsyncSession, obj_in: TTSProviderCreate) -> TTSProvider:
#     db_obj = TTSProvider(**obj_in.model_dump())
#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)
#     return db_obj

# async def update_tts_provider(db: AsyncSession, id: UUID, obj_in: TTSProviderUpdate) -> Optional[TTSProvider]:
#     update_data = obj_in.model_dump(exclude_unset=True)
#     if not update_data:
#         return await get_tts_provider(db, id)
#     await db.execute(update(TTSProvider).where(TTSProvider.id == id).values(**update_data))
#     await db.commit()
#     return await get_tts_provider(db, id)

# async def delete_tts_provider(db: AsyncSession, id: UUID) -> bool:
#     result = await db.execute(delete(TTSProvider).where(TTSProvider.id == id))
#     await db.commit()
#     return result.rowcount > 0

# # STT CRUD
# async def get_stt_providers(db: AsyncSession) -> List[STTProvider]:
#     result = await db.execute(select(STTProvider))
#     return result.scalars().all()

# async def get_stt_provider(db: AsyncSession, id: UUID) -> Optional[STTProvider]:
#     result = await db.execute(select(STTProvider).where(STTProvider.id == id))
#     return result.scalar_one_or_none()

# async def create_stt_provider(db: AsyncSession, obj_in: STTProviderCreate) -> STTProvider:
#     db_obj = STTProvider(**obj_in.model_dump())
#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)
#     return db_obj

# async def update_stt_provider(db: AsyncSession, id: UUID, obj_in: STTProviderUpdate) -> Optional[STTProvider]:
#     update_data = obj_in.model_dump(exclude_unset=True)
#     if not update_data:
#         return await get_stt_provider(db, id)
#     await db.execute(update(STTProvider).where(STTProvider.id == id).values(**update_data))
#     await db.commit()
#     return await get_stt_provider(db, id)

# async def delete_stt_provider(db: AsyncSession, id: UUID) -> bool:
#     result = await db.execute(delete(STTProvider).where(STTProvider.id == id))
#     await db.commit()
#     return result.rowcount > 0



from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, delete, exists, update
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from ..models import LLMProvider, TTSProvider, STTProvider, AgentProfile
from ..schemas.providers import (
    LLMProviderCreate, LLMProviderUpdate,
    TTSProviderCreate, TTSProviderUpdate,
    STTProviderCreate, STTProviderUpdate
)
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json


# Redis client (configure based on your Docker setup)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@asynccontextmanager
async def get_redis():
    try:
        yield redis_client
    finally:
        pass  # Redis connection is managed by the pool

# LLM CRUD
async def get_llm_providers(db: AsyncSession, redis: redis.Redis = None) -> List[LLMProvider]:
    if redis:
        cached = await redis.get("llm_providers")
        if cached:
            return [LLMProvider(**json.loads(cached))]
    result = await db.execute(select(LLMProvider))
    providers = result.scalars().all()
    if redis:
        await redis.set("llm_providers", json.dumps([p.__dict__ for p in providers]), ex=3600)
    return providers

async def get_llm_provider(db: AsyncSession, id: UUID) -> Optional[LLMProvider]:
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == id))
    return result.scalar_one_or_none()

async def create_llm_provider(db: AsyncSession, obj_in: LLMProviderCreate, redis: redis.Redis = None) -> LLMProvider:
    db_obj = LLMProvider()  # Create empty instance
    db_obj.provider = obj_in.provider  # Set attributes manually
    db_obj.models = obj_in.models
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    if redis:
        await redis.delete("llm_providers")  # Invalidate cache
    return db_obj

async def update_llm_provider(db: AsyncSession, id: UUID, obj_in: LLMProviderUpdate, redis: redis.Redis = None) -> Optional[LLMProvider]:
    update_data = obj_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_llm_provider(db, id)
    await db.execute(update(LLMProvider).where(LLMProvider.id == id).values(**update_data))
    await db.commit()
    if redis:
        await redis.delete("llm_providers")
    return await get_llm_provider(db, id)

async def delete_llm_provider(db: AsyncSession, id: UUID, redis: redis.Redis = None) -> bool:
    # Check if provider is in use
    result = await db.execute(select(AgentProfile).where(AgentProfile.llm_provider_id == id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cannot delete LLM provider in use by an agent profile")
    result = await db.execute(delete(LLMProvider).where(LLMProvider.id == id))
    await db.commit()
    if redis:
        await redis.delete("llm_providers")
    return result.rowcount > 0

# TTS CRUD
async def get_tts_providers(db: AsyncSession, redis: redis.Redis = None) -> List[TTSProvider]:
    if redis:
        cached = await redis.get("tts_providers")
        if cached:
            return [TTSProvider(**json.loads(cached))]
    result = await db.execute(select(TTSProvider))
    providers = result.scalars().all()
    if redis:
        await redis.set("tts_providers", json.dumps([p.__dict__ for p in providers]), ex=3600)
    return providers

async def get_tts_provider(db: AsyncSession, id: UUID) -> Optional[TTSProvider]:
    result = await db.execute(select(TTSProvider).where(TTSProvider.id == id))
    return result.scalar_one_or_none()

# async def create_tts_provider(db: AsyncSession, obj_in: TTSProviderCreate, redis: redis.Redis = None) -> TTSProvider:
#     db_obj = TTSProvider()  # Create empty instance
#     db_obj.provider = obj_in.provider  # Set attributes manually
#     db_obj.models = obj_in.models
#     db_obj.voices = obj_in.voices
#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)
#     if redis:
#         await redis.delete("tts_providers")
#     return db_obj

async def create_tts_provider(db: AsyncSession, obj_in: TTSProviderCreate, redis: redis.Redis = None) -> TTSProvider:
    db_obj = TTSProvider()
    db_obj.provider = obj_in.provider

    # Correctly convert Pydantic models to dictionaries
    db_obj.models = [m.model_dump() for m in obj_in.models]
    db_obj.voices = [v.model_dump() for v in obj_in.voices]

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    if redis:
        await redis.delete("tts_providers")
    return db_obj
    
async def update_tts_provider(db: AsyncSession, id: UUID, obj_in: TTSProviderUpdate, redis: redis.Redis = None) -> Optional[TTSProvider]:
    update_data = obj_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_tts_provider(db, id)
    await db.execute(update(TTSProvider).where(TTSProvider.id == id).values(**update_data))
    await db.commit()
    if redis:
        await redis.delete("tts_providers")
    return await get_tts_provider(db, id)

async def delete_tts_provider(db: AsyncSession, id: UUID, redis: redis.Redis = None) -> bool:
    """
    Deletes a TTS provider using the standard LBYL pattern with exists().
    """
    # 1. Create a query to efficiently check if any AgentProfile uses this provider.
    is_in_use_query = select(exists().where(AgentProfile.tts_provider_id == id))
    
    # 2. Execute the query. `.scalar()` directly returns the boolean True/False result.
    is_in_use = await db.scalar(is_in_use_query)

    # 3. "Leap" only if the condition is met (the provider is not in use).
    if is_in_use:
        # 409 Conflict is often a more semantically correct status code for this situation.
        raise HTTPException(
            status_code=409,  
            detail="Cannot delete TTS provider. It is still in use by one or more agent profiles."
        )

    # If not in use, proceed with the deletion.
    result = await db.execute(
        delete(TTSProvider).where(TTSProvider.id == id)
    )
    await db.commit()

    if redis:
        await redis.delete("tts_providers")

    # result.rowcount will be 1 if a row was deleted, 0 if it wasn't found.
    return result.rowcount > 0


# async def delete_tts_provider(db: AsyncSession, id: UUID, redis: redis.Redis = None) -> bool:
#     result = await db.execute(select(AgentProfile).where(AgentProfile.tts_provider_id == id))
#     if result.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="Cannot delete TTS provider in use by an agent profile")
#     result = await db.execute(delete(TTSProvider).where(TTSProvider.id == id))
#     await db.commit()
#     if redis:
#         await redis.delete("tts_providers")
#     return result.rowcount > 0

# STT CRUD
async def get_stt_providers(db: AsyncSession, redis: redis.Redis = None) -> List[STTProvider]:
    if redis:
        cached = await redis.get("stt_providers")
        if cached:
            return [STTProvider(**json.loads(cached))]
    result = await db.execute(select(STTProvider))
    providers = result.scalars().all()
    if redis:
        await redis.set("stt_providers", json.dumps([p.__dict__ for p in providers]), ex=3600)
    return providers

async def get_stt_provider(db: AsyncSession, id: UUID) -> Optional[STTProvider]:
    result = await db.execute(select(STTProvider).where(STTProvider.id == id))
    return result.scalar_one_or_none()

# async def create_stt_provider(db: AsyncSession, obj_in: STTProviderCreate, redis: redis.Redis = None) -> STTProvider:
#     db_obj = STTProvider()  # Create empty instance
#     db_obj.provider = obj_in.provider  # Set attributes manually
#     db_obj.models = obj_in.models
#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)
#     if redis:
#         await redis.delete("stt_providers")
#     return db_obj

async def create_stt_provider(db: AsyncSession, obj_in: STTProviderCreate, redis: redis.Redis = None) -> STTProvider:
    """
    Creates a new STT provider, checking for duplicates first.
    """
    # Check if a provider with this name already exists.
    existing_provider_stmt = select(STTProvider).where(STTProvider.provider == obj_in.provider)
    result = await db.execute(existing_provider_stmt)
    
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Provider '{obj_in.provider}' already exists."
        )

    # Convert the list of model objects to a list of dictionaries
    models_as_dicts = [model.model_dump() for model in obj_in.models]
    
    # 1. Create an empty instance of the SQLAlchemy model.
    db_obj = STTProvider()
    
    # 2. Set the attributes on the instance individually.
    db_obj.provider = obj_in.provider
    db_obj.models = models_as_dicts
    
    # 3. Add to the session and commit.
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    if redis:
        await redis.delete("stt_providers")
        
    return db_obj

async def update_stt_provider(db: AsyncSession, id: UUID, obj_in: STTProviderUpdate, redis: redis.Redis = None) -> Optional[STTProvider]:
    update_data = obj_in.model_dump(exclude_unset=True)
    if not update_data:
        return await get_stt_provider(db, id)
    await db.execute(update(STTProvider).where(STTProvider.id == id).values(**update_data))
    await db.commit()
    if redis:
        await redis.delete("stt_providers")
    return await get_stt_provider(db, id)

# async def delete_stt_provider(db: AsyncSession, id: UUID, redis: redis.Redis = None) -> bool:
#     result = await db.execute(select(AgentProfile).where(AgentProfile.stt_provider_id == id))
#     if result.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="Cannot delete STT provider in use by an agent profile")
#     result = await db.execute(delete(STTProvider).where(STTProvider.id == id))
#     await db.commit()
#     if redis:
#         await redis.delete("stt_providers")
#     return result.rowcount > 0


async def delete_stt_provider(db: AsyncSession, id: UUID, redis: redis.Redis = None) -> bool:
    """
    Deletes an STT provider, but only if it's not in use by any agent profile.
    """
    # 1. Create an `exists` query to efficiently check if the provider is in use.
    is_in_use_query = select(exists().where(AgentProfile.stt_provider_id == id))
    
    # 2. Execute the query to get a simple True/False result.
    is_in_use = await db.scalar(is_in_use_query)

    # 3. If it's in use, raise a user-friendly error.
    if is_in_use:
        raise HTTPException(
            status_code=409,  # 409 Conflict is the correct status code here
            detail="Cannot delete STT provider. It is still in use by one or more agent profiles."
        )

    # 4. If not in use, proceed with the deletion.
    result = await db.execute(
        delete(STTProvider).where(STTProvider.id == id)
    )
    await db.commit()

    if redis:
        await redis.delete("stt_providers")

    # result.rowcount will be 1 if a row was deleted, 0 otherwise.
    return result.rowcount > 0
