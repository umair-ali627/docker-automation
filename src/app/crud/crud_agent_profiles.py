# # app/crud/crud_agent_profiles.py
# from typing import Dict, List, Optional, Any, Union
# import uuid
# from fastapi import HTTPException
# from sqlalchemy import and_, update , select
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastcrud import FastCRUD

# from ..models.agent_profile import AgentProfile
# from ..schemas.agent_profile import (
#     AgentProfileCreate, 
#     AgentProfileCreateInternal,
#     AgentProfileUpdate, 
#     AgentProfileUpdateInternal,
#     AgentProfileDelete,
#     AgentProfileInDB
# )
# from ..schemas.provider_types import LLMProvider, TTSProvider, STTProvider


# class CRUDAgentProfileExtended(FastCRUD[
#     AgentProfile,  # Model
#     AgentProfileCreateInternal,  # Create Schema
#     AgentProfileUpdate,  # Update Schema
#     AgentProfileUpdateInternal,  # Internal Update Schema
#     AgentProfileDelete,  # Delete Schema
#     AgentProfileInDB  # Read Schema
# ]):
#     async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AgentProfileInDB]:
#         """Get an agent profile by name."""
#         profile = await super().get(
#             db=db, 
#             name=name
#         )
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def get_default(self, db: AsyncSession) -> Optional[AgentProfileInDB]:
#         """Get the default agent profile."""
#         profile = await super().get(
#             db=db, 
#             is_default=True
#         )
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def get_multi(
#         self, db: AsyncSession, *, skip: int = 0, limit: int = 100, owner_id: Optional[uuid.UUID] = None
#     ) -> List[AgentProfileInDB]:
#         """Get multiple agent profiles with optional owner filter."""
#         filters = {}
#         if owner_id is not None:
#             filters["owner_id"] = owner_id
            
#         result = await super().get_multi(
#             db=db,
#             offset=skip,
#             limit=limit,
#             **filters
#         )
        
#         profiles = []
#         for item in result["data"]:
#             profiles.append(AgentProfileInDB.model_validate(item))
            
#         return profiles

#     async def create(self, db: AsyncSession, *, obj_in: AgentProfileCreate, owner_id: uuid.UUID) -> AgentProfileInDB:
#         """Create a new agent profile with handling for default status and provider options."""
#         # If this profile is set as default, make all others non-default for this owner
#         if obj_in.is_default:
#             await db.execute(
#                 update(AgentProfile)
#                 .where(AgentProfile.owner_id == owner_id)
#                 .values(is_default=False)
#             )
        
#         # Create internal schema with owner_id
#         internal_obj = AgentProfileCreateInternal(
#             **{k: v for k, v in obj_in.model_dump().items() if k != 'id'},
#             owner_id=owner_id
#         )
        
#         # Create using the FastCRUD base method
#         new_profile = await super().create(db=db, object=internal_obj)
        
#         return AgentProfileInDB.model_validate(new_profile)

#     async def update(
#         self, db: AsyncSession, *, id: uuid.UUID, obj_in: AgentProfileUpdate, owner_id: Optional[uuid.UUID] = None
#     ) -> AgentProfileInDB:
#         """Update an agent profile with handling for default status and provider options."""
#         # Get the profile
#         db_obj = await self.get(
#             db=db, 
#             id=id
#         )
#         if not db_obj:
#             raise HTTPException(status_code=404, detail="Agent profile not found")
        
#         # Check ownership if owner_id provided
#         if owner_id is not None and db_obj.owner_id != owner_id:
#             raise HTTPException(status_code=403, detail="Not enough permissions")
        
#         # Handle default status
#         if obj_in.is_default:
#             await db.execute(
#                 update(AgentProfile)
#                 .where(and_(
#                     AgentProfile.owner_id == db_obj.owner_id,
#                     AgentProfile.id != id
#                 ))
#                 .values(is_default=False)
#             )
        
#         # Special handling for provider options
#         update_data = obj_in.model_dump(exclude_unset=True)
        
#         # If provider has changed, initialize options with defaults
#         if 'llm_provider' in update_data and update_data['llm_provider'] != db_obj.llm_provider:
#             from ..schemas.provider_types import LLMProvider
#             if update_data['llm_provider'] == LLMProvider.OPENAI:
#                 from ..schemas.agent_profile import OpenAILLMOptions
#                 update_data['llm_options'] = OpenAILLMOptions().model_dump()
#             elif update_data['llm_provider'] == LLMProvider.GOOGLE:
#                 from ..schemas.agent_profile import GoogleLLMOptions
#                 update_data['llm_options'] = GoogleLLMOptions().model_dump()
                
#         if 'tts_provider' in update_data and update_data['tts_provider'] != db_obj.tts_provider:
#             from ..schemas.provider_types import TTSProvider
#             if update_data['tts_provider'] == TTSProvider.OPENAI:
#                 from ..schemas.agent_profile import OpenAITTSOptions
#                 update_data['tts_options'] = OpenAITTSOptions().model_dump()
#             elif update_data['tts_provider'] == TTSProvider.GOOGLE:
#                 from ..schemas.agent_profile import GoogleTTSOptions
#                 update_data['tts_options'] = GoogleTTSOptions().model_dump()
                
#         if 'stt_provider' in update_data and update_data['stt_provider'] != db_obj.stt_provider:
#             from ..schemas.provider_types import STTProvider
#             if update_data['stt_provider'] == STTProvider.DEEPGRAM:
#                 from ..schemas.agent_profile import DeepgramSTTOptions
#                 update_data['stt_options'] = DeepgramSTTOptions().model_dump()
#             elif update_data['stt_provider'] == STTProvider.GOOGLE:
#                 from ..schemas.agent_profile import GoogleSTTOptions
#                 update_data['stt_options'] = GoogleSTTOptions().model_dump()
        
#         # Merge options if provided
#         if 'llm_options' in update_data and isinstance(update_data['llm_options'], dict) and db_obj.llm_options:
#             merged_options = db_obj.llm_options.copy()
#             merged_options.update(update_data['llm_options'])
#             update_data['llm_options'] = merged_options
            
#         if 'tts_options' in update_data and isinstance(update_data['tts_options'], dict) and db_obj.tts_options:
#             merged_options = db_obj.tts_options.copy()
#             merged_options.update(update_data['tts_options'])
#             update_data['tts_options'] = merged_options
            
#         if 'stt_options' in update_data and isinstance(update_data['stt_options'], dict) and db_obj.stt_options:
#             merged_options = db_obj.stt_options.copy()
#             merged_options.update(update_data['stt_options'])
#             update_data['stt_options'] = merged_options
            
#         # Create update object
#         update_obj = AgentProfileUpdateInternal(**update_data)
        
#         # Use the FastCRUD update method
#         updated_profile = await super().update(
#             db=db, 
#             id=id, 
#             object=update_obj
#         )

#         result = await db.execute(
#             select(AgentProfile).where(
#                 and_(
#                     AgentProfile.id == id,
#                     AgentProfile.owner_id == owner_id
#                 )
#             )
#         )
#         updated_profile = result.scalar_one_or_none()
#         await db.commit()
        
#         if updated_profile:
#             return AgentProfileInDB.model_validate(updated_profile)
        
#         return updated_profile

#     async def get(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
#         """Get an agent profile by ID."""
#         profile = await super().get(
#             db=db, 
#             id=id
#         )
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
#         """Delete an agent profile by ID."""
#         # First get the profile to return it after deletion
#         profile = await self.get(db=db, id=id)
#         if not profile:
#             return None
            
#         await super().delete(db=db, id=id)
#         return profile


# # Create a singleton CRUD instance
# crud_agent_profiles = CRUDAgentProfileExtended(AgentProfile)



# befote the provider and id object 
# from typing import List, Optional
# import uuid
# from fastapi import HTTPException
# from sqlalchemy import and_, update, select
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastcrud import FastCRUD

# from ..models.agent_profile import AgentProfile
# from ..models import LLMProvider, TTSProvider, STTProvider
# from ..schemas.agent_profile import (
#     AgentProfileCreate,
#     AgentProfileCreateInternal,
#     AgentProfileUpdate,
#     AgentProfileUpdateInternal,
#     AgentProfileDelete,
#     AgentProfileInDB,
# )

# class CRUDAgentProfileExtended(FastCRUD[
#     AgentProfile,  # Model
#     AgentProfileCreateInternal,  # Create Schema
#     AgentProfileUpdate,  # Update Schema
#     AgentProfileUpdateInternal,  # Internal Update Schema
#     AgentProfileDelete,  # Delete Schema
#     AgentProfileInDB  # Read Schema
# ]):
#     async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AgentProfileInDB]:
#         """Get an agent profile by name."""
#         profile = await super().get(db=db, name=name)
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def get_default(self, db: AsyncSession) -> Optional[AgentProfileInDB]:
#         """Get the default agent profile."""
#         profile = await super().get(db=db, is_default=True)
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def get_multi(
#         self, db: AsyncSession, *, skip: int = 0, limit: int = 100, owner_id: Optional[uuid.UUID] = None
#     ) -> List[AgentProfileInDB]:
#         """Get multiple agent profiles with optional owner filter."""
#         filters = {}
#         if owner_id is not None:
#             filters["owner_id"] = owner_id

#         result = await super().get_multi(
#             db=db,
#             offset=skip,
#             limit=limit,
#             **filters
#         )

#         profiles = []
#         for item in result["data"]:
#             profiles.append(AgentProfileInDB.model_validate(item))

#         return profiles

#     async def create(self, db: AsyncSession, *, obj_in: AgentProfileCreate, owner_id: uuid.UUID) -> AgentProfileInDB:
#         """Create a new agent profile with validation for provider IDs."""
#         # Validate provider IDs
#         llm_provider = await db.execute(select(LLMProvider).where(LLMProvider.id == obj_in.llm_provider_id))
#         if not llm_provider.scalar_one_or_none():
#             raise HTTPException(status_code=400, detail="Invalid llm_provider_id")
#         tts_provider = await db.execute(select(TTSProvider).where(TTSProvider.id == obj_in.tts_provider_id))
#         if not tts_provider.scalar_one_or_none():
#             raise HTTPException(status_code=400, detail="Invalid tts_provider_id")
#         stt_provider = await db.execute(select(STTProvider).where(STTProvider.id == obj_in.stt_provider_id))
#         if not stt_provider.scalar_one_or_none():
#             raise HTTPException(status_code=400, detail="Invalid stt_provider_id")

#         # Validate options against provider models/voices
#         await self._validate_options(db, obj_in.llm_provider_id, obj_in.tts_provider_id, obj_in.stt_provider_id, obj_in)

#         # If this profile is set as default, make all others non-default for this owner
#         if obj_in.is_default:
#             await db.execute(
#                 update(AgentProfile)
#                 .where(AgentProfile.owner_id == owner_id)
#                 .values(is_default=False)
#             )

#         # Create internal schema with owner_id
#         internal_obj = AgentProfileCreateInternal(
#             **{k: v for k, v in obj_in.model_dump().items() if k != 'id'},
#             owner_id=owner_id
#         )

#         # Create using the FastCRUD base method
#         new_profile = await super().create(db=db, object=internal_obj)

#         return AgentProfileInDB.model_validate(new_profile)

#     async def update(
#         self, db: AsyncSession, *, id: uuid.UUID, obj_in: AgentProfileUpdate, owner_id: Optional[uuid.UUID] = None
#     ) -> AgentProfileInDB:
#         """Update an agent profile with validation for provider IDs and options."""
#         # Get the profile
#         db_obj = await self.get(db=db, id=id)
#         if not db_obj:
#             raise HTTPException(status_code=404, detail="Agent profile not found")

#         # Check ownership if owner_id provided
#         if owner_id is not None and db_obj.owner_id != owner_id:
#             raise HTTPException(status_code=403, detail="Not enough permissions")

#         # Handle default status
#         if obj_in.is_default:
#             await db.execute(
#                 update(AgentProfile)
#                 .where(and_(
#                     AgentProfile.owner_id == db_obj.owner_id,
#                     AgentProfile.id != id
#                 ))
#                 .values(is_default=False)
#             )

#         # Prepare update data
#         update_data = obj_in.model_dump(exclude_unset=True)

#         # Validate provider IDs if provided
#         llm_provider_id = update_data.get('llm_provider_id', db_obj.llm_provider_id)
#         tts_provider_id = update_data.get('tts_provider_id', db_obj.tts_provider_id)
#         stt_provider_id = update_data.get('stt_provider_id', db_obj.stt_provider_id)

#         llm_provider = await db.execute(select(LLMProvider).where(LLMProvider.id == llm_provider_id))
#         if not llm_provider.scalar_one_or_none():
#             raise HTTPException(status_code=400, detail="Invalid llm_provider_id")
#         tts_provider = await db.execute(select(TTSProvider).where(TTSProvider.id == tts_provider_id))
#         if not tts_provider.scalar_one_or_none():
#             raise HTTPException(status_code=400, detail="Invalid tts_provider_id")
#         stt_provider = await db.execute(select(STTProvider).where(STTProvider.id == stt_provider_id))
#         if not stt_provider.scalar_one_or_none():
#             raise HTTPException(status_code=400, detail="Invalid stt_provider_id")

#         # Validate options against provider models/voices
#         await self._validate_options(db, llm_provider_id, tts_provider_id, stt_provider_id, obj_in)

#         # Merge options if provided
#         if 'llm_options' in update_data and isinstance(update_data['llm_options'], dict) and db_obj.llm_options:
#             merged_options = db_obj.llm_options.copy()
#             merged_options.update(update_data['llm_options'])
#             update_data['llm_options'] = merged_options

#         if 'tts_options' in update_data and isinstance(update_data['tts_options'], dict) and db_obj.tts_options:
#             merged_options = db_obj.tts_options.copy()
#             merged_options.update(update_data['tts_options'])
#             update_data['tts_options'] = merged_options

#         if 'stt_options' in update_data and isinstance(update_data['stt_options'], dict) and db_obj.stt_options:
#             merged_options = db_obj.stt_options.copy()
#             merged_options.update(update_data['stt_options'])
#             update_data['stt_options'] = merged_options

#         # Create update object
#         update_obj = AgentProfileUpdateInternal(**update_data)

#         # Use the FastCRUD update method
#         updated_profile = await super().update(db=db, id=id, object=update_obj)

#         result = await db.execute(
#             select(AgentProfile).where(
#                 and_(
#                     AgentProfile.id == id,
#                     AgentProfile.owner_id == owner_id if owner_id else True
#                 )
#             )
#         )
#         updated_profile = result.scalar_one_or_none()
#         await db.commit()

#         if updated_profile:
#             return AgentProfileInDB.model_validate(updated_profile)

#         return updated_profile

#     async def get(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
#         """Get an agent profile by ID."""
#         profile = await super().get(db=db, id=id)
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
#         """Delete an agent profile by ID."""
#         profile = await self.get(db=db, id=id)
#         if not profile:
#             return None

#         await super().delete(db=db, id=id)
#         return profile

#     async def _validate_options(
#         self, db: AsyncSession, llm_provider_id: uuid.UUID, tts_provider_id: uuid.UUID, stt_provider_id: uuid.UUID, obj_in: AgentProfileCreate | AgentProfileUpdate
#     ) -> None:
#         """Validate llm_options, tts_options, and stt_options against provider models and voices."""
#         # Fetch providers
#         llm_provider = (await db.execute(select(LLMProvider).where(LLMProvider.id == llm_provider_id))).scalar_one_or_none()
#         tts_provider = (await db.execute(select(TTSProvider).where(TTSProvider.id == tts_provider_id))).scalar_one_or_none()
#         stt_provider = (await db.execute(select(STTProvider).where(STTProvider.id == stt_provider_id))).scalar_one_or_none()

#         # Validate llm_options
#         if hasattr(obj_in, 'llm_options') and obj_in.llm_options and 'model' in obj_in.llm_options:
#             if not llm_provider or obj_in.llm_options['model'] not in llm_provider.models:
#                 raise HTTPException(status_code=400, detail=f"Invalid model in llm_options: {obj_in.llm_options['model']}")

#         # Validate tts_options
#         if hasattr(obj_in, 'tts_options') and obj_in.tts_options:
#             if 'model' in obj_in.tts_options:
#                 if not tts_provider or not any(m['model'] == obj_in.tts_options['model'] for m in tts_provider.models):
#                     raise HTTPException(status_code=400, detail=f"Invalid model in tts_options: {obj_in.tts_options['model']}")
#             if 'voice' in obj_in.tts_options:
#                 if not tts_provider or not any(v['id'] == obj_in.tts_options['voice'] for v in tts_provider.voices):
#                     raise HTTPException(status_code=400, detail=f"Invalid voice in tts_options: {obj_in.tts_options['voice']}")

#         # Validate stt_options
#         if hasattr(obj_in, 'stt_options') and obj_in.stt_options and 'model' in obj_in.stt_options:
#             if not stt_provider or not any(m['model'] == obj_in.stt_options['model'] for m in stt_provider.models):
#                 raise HTTPException(status_code=400, detail=f"Invalid model in stt_options: {obj_in.stt_options['model']}")

# # Create a singleton CRUD instance
# crud_agent_profiles = CRUDAgentProfileExtended(AgentProfile)



# after the provider and id object correct with create only

# from typing import List, Optional
# import uuid
# from fastapi import HTTPException
# from sqlalchemy import and_, update, select
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastcrud import FastCRUD

# from ..models.agent_profile import AgentProfile
# from ..models import LLMProvider, TTSProvider, STTProvider
# from ..schemas.agent_profile import (
#     AgentProfileCreate,
#     AgentProfileCreateInternal,
#     AgentProfileUpdate,
#     AgentProfileUpdateInternal,
#     AgentProfileDelete,
#     AgentProfileInDB,
# )

# class CRUDAgentProfileExtended(FastCRUD[
#     AgentProfile,  # Model
#     AgentProfileCreateInternal,  # Create Schema
#     AgentProfileUpdate,  # Update Schema
#     AgentProfileUpdateInternal,  # Internal Update Schema
#     AgentProfileDelete,  # Delete Schema
#     AgentProfileInDB  # Read Schema
# ]):
#     async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AgentProfileInDB]:
#         """Get an agent profile by name."""
#         profile = await super().get(db=db, name=name)
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def get_default(self, db: AsyncSession) -> Optional[AgentProfileInDB]:
#         """Get the default agent profile."""
#         profile = await super().get(db=db, is_default=True)
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def get_multi(
#         self, db: AsyncSession, *, skip: int = 0, limit: int = 100, owner_id: Optional[uuid.UUID] = None
#     ) -> List[AgentProfileInDB]:
#         """Get multiple agent profiles with optional owner filter."""
#         filters = {}
#         if owner_id is not None:
#             filters["owner_id"] = owner_id

#         result = await super().get_multi(
#             db=db,
#             offset=skip,
#             limit=limit,
#             **filters
#         )

#         profiles = []
#         for item in result["data"]:
#             profiles.append(AgentProfileInDB.model_validate(item))

#         return profiles



#     async def create(self, db: AsyncSession, *, obj_in: AgentProfileCreate, owner_id: uuid.UUID) -> AgentProfileInDB:
#         """Create a new agent profile with validation for provider IDs."""
#         # Validate provider IDs
#         llm_provider = await db.execute(select(LLMProvider).where(LLMProvider.id == obj_in.llm_provider.id))
#         llm_provider_obj = llm_provider.scalar_one_or_none()
#         if not llm_provider_obj:
#             raise HTTPException(status_code=400, detail="Invalid llm_provider_id")
#         if llm_provider_obj.provider != obj_in.llm_provider.provider:
#             raise HTTPException(status_code=400, detail="llm_provider name mismatch")

#         tts_provider = await db.execute(select(TTSProvider).where(TTSProvider.id == obj_in.tts_provider.id))
#         tts_provider_obj = tts_provider.scalar_one_or_none()
#         if not tts_provider_obj:
#             raise HTTPException(status_code=400, detail="Invalid tts_provider_id")
#         if tts_provider_obj.provider != obj_in.tts_provider.provider:
#             raise HTTPException(status_code=400, detail="tts_provider name mismatch")

#         stt_provider = await db.execute(select(STTProvider).where(STTProvider.id == obj_in.stt_provider.id))
#         stt_provider_obj = stt_provider.scalar_one_or_none()
#         if not stt_provider_obj:
#             raise HTTPException(status_code=400, detail="Invalid stt_provider_id")
#         if stt_provider_obj.provider != obj_in.stt_provider.provider:
#             raise HTTPException(status_code=400, detail="stt_provider name mismatch")

#         # Validate options against provider models/voices
#         await self._validate_options(db, obj_in.llm_provider.id, obj_in.tts_provider.id, obj_in.stt_provider.id, obj_in)

#         # If this profile is set as default, make all others non-default for this owner
#         if obj_in.is_default:
#             await db.execute(
#                 update(AgentProfile)
#                 .where(AgentProfile.owner_id == owner_id)
#                 .values(is_default=False)
#             )

#         # Create internal schema with owner_id and provider IDs
#         internal_data = obj_in.model_dump(exclude={"llm_provider", "tts_provider", "stt_provider"})
#         internal_data["owner_id"] = owner_id
#         internal_data["llm_provider_id"] = obj_in.llm_provider.id
#         internal_data["tts_provider_id"] = obj_in.tts_provider.id
#         internal_data["stt_provider_id"] = obj_in.stt_provider.id

#         # Create internal schema instance
#         internal_obj = AgentProfileCreateInternal(**internal_data)

#         # Create using the FastCRUD base method
#         new_profile = await super().create(db=db, object=internal_obj)

#         # Transform related objects to match ProviderBase schema
#         new_profile_dict = new_profile.__dict__.copy()
#         new_profile_dict["llm_provider"] = {"id": new_profile.llm_provider.id, "provider": new_profile.llm_provider.provider} if new_profile.llm_provider else None
#         new_profile_dict["tts_provider"] = {"id": new_profile.tts_provider.id, "provider": new_profile.tts_provider.provider} if new_profile.tts_provider else None
#         new_profile_dict["stt_provider"] = {"id": new_profile.stt_provider.id, "provider": new_profile.stt_provider.provider} if new_profile.stt_provider else None

#         return AgentProfileInDB.model_validate(new_profile_dict)

#     async def update(
#         self, db: AsyncSession, *, id: uuid.UUID, obj_in: AgentProfileUpdate, owner_id: Optional[uuid.UUID] = None
#     ) -> AgentProfileInDB:
#         """Update an agent profile with validation for provider IDs and options."""
#         # Get the profile
#         db_obj = await self.get(db=db, id=id)
#         if not db_obj:
#             raise HTTPException(status_code=404, detail="Agent profile not found")

#         # Check ownership if owner_id provided
#         if owner_id is not None and db_obj.owner_id != owner_id:
#             raise HTTPException(status_code=403, detail="Not enough permissions")

#         # Handle default status
#         if obj_in.is_default:
#             await db.execute(
#                 update(AgentProfile)
#                 .where(and_(
#                     AgentProfile.owner_id == db_obj.owner_id,
#                     AgentProfile.id != id
#                 ))
#                 .values(is_default=False)
#             )

#         # Prepare update data
#         update_data = obj_in.model_dump(exclude_unset=True)

#         # Validate provider IDs if provided
#         llm_provider_id = db_obj.llm_provider_id
#         tts_provider_id = db_obj.tts_provider_id
#         stt_provider_id = db_obj.stt_provider_id

#         if 'llm_provider' in update_data:
#             llm_provider_id = update_data['llm_provider'].id
#             llm_provider = await db.execute(select(LLMProvider).where(LLMProvider.id == llm_provider_id))
#             if not llm_provider.scalar_one_or_none():
#                 raise HTTPException(status_code=400, detail="Invalid llm_provider_id")
#             llm_provider_obj = llm_provider.scalar_one_or_none()
#             if llm_provider_obj and llm_provider_obj.provider != update_data['llm_provider'].provider:
#                 raise HTTPException(status_code=400, detail="llm_provider name mismatch")

#         if 'tts_provider' in update_data:
#             tts_provider_id = update_data['tts_provider'].id
#             tts_provider = await db.execute(select(TTSProvider).where(TTSProvider.id == tts_provider_id))
#             if not tts_provider.scalar_one_or_none():
#                 raise HTTPException(status_code=400, detail="Invalid tts_provider_id")
#             tts_provider_obj = tts_provider.scalar_one_or_none()
#             if tts_provider_obj and tts_provider_obj.provider != update_data['tts_provider'].provider:
#                 raise HTTPException(status_code=400, detail="tts_provider name mismatch")

#         if 'stt_provider' in update_data:
#             stt_provider_id = update_data['stt_provider'].id
#             stt_provider = await db.execute(select(STTProvider).where(STTProvider.id == stt_provider_id))
#             if not stt_provider.scalar_one_or_none():
#                 raise HTTPException(status_code=400, detail="Invalid stt_provider_id")
#             stt_provider_obj = stt_provider.scalar_one_or_none()
#             if stt_provider_obj and stt_provider_obj.provider != update_data['stt_provider'].provider:
#                 raise HTTPException(status_code=400, detail="stt_provider name mismatch")

#         # Validate options against provider models/voices
#         await self._validate_options(db, llm_provider_id, tts_provider_id, stt_provider_id, obj_in)

#         # Merge options if provided
#         if 'llm_options' in update_data and isinstance(update_data['llm_options'], dict) and db_obj.llm_options:
#             merged_options = db_obj.llm_options.copy()
#             merged_options.update(update_data['llm_options'])
#             update_data['llm_options'] = merged_options

#         if 'tts_options' in update_data and isinstance(update_data['tts_options'], dict) and db_obj.tts_options:
#             merged_options = db_obj.tts_options.copy()
#             merged_options.update(update_data['tts_options'])
#             update_data['tts_options'] = merged_options

#         if 'stt_options' in update_data and isinstance(update_data['stt_options'], dict) and db_obj.stt_options:
#             merged_options = db_obj.stt_options.copy()
#             merged_options.update(update_data['stt_options'])
#             update_data['stt_options'] = merged_options

#         # Create update object
#         update_obj = AgentProfileUpdateInternal(**update_data)

#         # Use the FastCRUD update method
#         updated_profile = await super().update(db=db, id=id, object=update_obj)

#         result = await db.execute(
#             select(AgentProfile).where(
#                 and_(
#                     AgentProfile.id == id,
#                     AgentProfile.owner_id == owner_id if owner_id else True
#                 )
#             )
#         )
#         updated_profile = result.scalar_one_or_none()
#         await db.commit()

#         if updated_profile:
#             return AgentProfileInDB.model_validate(updated_profile)

#         return updated_profile

#     async def get(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
#         """Get an agent profile by ID."""
#         result = await db.execute(
#             select(AgentProfile)
#             .options(selectinload(AgentProfile.llm_provider), selectinload(AgentProfile.tts_provider), selectinload(AgentProfile.stt_provider))
#             .where(AgentProfile.id == id)
#         )
#         profile = result.scalars().first()
#         if profile:
#             return AgentProfileInDB.model_validate(profile)
#         return None

#     async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
#         """Delete an agent profile by ID."""
#         profile = await self.get(db=db, id=id)
#         if not profile:
#             return None

#         await super().delete(db=db, id=id)
#         return profile

#     async def _validate_options(
#         self, db: AsyncSession, llm_provider_id: uuid.UUID, tts_provider_id: uuid.UUID, stt_provider_id: uuid.UUID, obj_in: AgentProfileCreate | AgentProfileUpdate
#     ) -> None:
#         """Validate llm_options, tts_options, and stt_options against provider models and voices."""
#         # Fetch providers
#         llm_provider = (await db.execute(select(LLMProvider).where(LLMProvider.id == llm_provider_id))).scalar_one_or_none()
#         tts_provider = (await db.execute(select(TTSProvider).where(TTSProvider.id == tts_provider_id))).scalar_one_or_none()
#         stt_provider = (await db.execute(select(STTProvider).where(STTProvider.id == stt_provider_id))).scalar_one_or_none()

#         # Validate llm_options
#         if hasattr(obj_in, 'llm_options') and obj_in.llm_options and 'model' in obj_in.llm_options:
#             if not llm_provider or obj_in.llm_options['model'] not in llm_provider.models:
#                 raise HTTPException(status_code=400, detail=f"Invalid model in llm_options: {obj_in.llm_options['model']}")

#         # Validate tts_options
#         if hasattr(obj_in, 'tts_options') and obj_in.tts_options:
#             if 'model' in obj_in.tts_options:
#                 if not tts_provider or not any(m['model'] == obj_in.tts_options['model'] for m in tts_provider.models):
#                     raise HTTPException(status_code=400, detail=f"Invalid model in tts_options: {obj_in.tts_options['model']}")
#             if 'voice' in obj_in.tts_options:
#                 if not tts_provider or not any(v['id'] == obj_in.tts_options['voice'] for v in tts_provider.voices):
#                     raise HTTPException(status_code=400, detail=f"Invalid voice in tts_options: {obj_in.tts_options['voice']}")

#         # Validate stt_options
#         if hasattr(obj_in, 'stt_options') and obj_in.stt_options and 'model' in obj_in.stt_options:
#             if not stt_provider or not any(m['model'] == obj_in.stt_options['model'] for m in stt_provider.models):
#                 raise HTTPException(status_code=400, detail=f"Invalid model in stt_options: {obj_in.stt_options['model']}")

# # Create a singleton CRUD instance
# crud_agent_profiles = CRUDAgentProfileExtended(AgentProfile)

from typing import List, Optional, Dict, Any
import uuid
import logging
from fastapi import HTTPException
from sqlalchemy import and_, func, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.call_logs import CallLog
from ..crud.crud_documents import crud_agent_knowledge_mapping
from fastcrud import FastCRUD


from ..models.document import KnowledgeBase, Document, AgentKnowledgeMapping
from ..schemas.document import KnowledgeBaseWithDocsRead, DocumentRead, DocumentWithContentRead
from sqlalchemy.orm import joinedload

from ..models.agent_profile import AgentProfile
from ..models import LLMProvider, TTSProvider, STTProvider
from ..schemas.agent_profile import (
    AgentProfileCreate,
    AgentProfileCreateInternal,
    AgentProfileUpdate,
    AgentProfileUpdateInternal,
    AgentProfileDelete,
    AgentProfileInDB,
    ProviderBase,
    TTSOptions,
    STTOptions
)

logger = logging.getLogger(__name__)
class CRUDAgentProfileExtended(FastCRUD[
    AgentProfile,
    AgentProfileCreateInternal,
    AgentProfileUpdate,
    AgentProfileUpdateInternal,
    AgentProfileDelete,
    AgentProfileInDB
]):
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AgentProfileInDB]:
        """Get an agent profile by name, excluding soft-deleted profiles."""
        result = await db.execute(
            select(AgentProfile)
            .options(
                selectinload(AgentProfile.llm_provider),
                selectinload(AgentProfile.tts_provider),
                selectinload(AgentProfile.stt_provider)
            )
            .where(AgentProfile.name == name, AgentProfile.is_deleted == False)
        )
        profile = result.scalars().first()
        if profile:
            return self._construct_profile(profile)
        return None

    async def get_default(self, db: AsyncSession) -> Optional[AgentProfileInDB]:
        """Get the default agent profile."""
        profile = await super().get(db=db, is_default=True)
        if profile:
            return self._construct_profile(profile)
        return None

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, owner_id: Optional[uuid.UUID] = None
    ) -> List[AgentProfileInDB]:
        """Get multiple agent profiles, excluding soft-deleted profiles."""
        query = select(AgentProfile).options(
            selectinload(AgentProfile.llm_provider),
            selectinload(AgentProfile.tts_provider),
            selectinload(AgentProfile.stt_provider)
        ).where(AgentProfile.is_deleted == False)
        if owner_id is not None:
            query = query.where(AgentProfile.owner_id == owner_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()
        profiles = [self._construct_profile(item) for item in items]
        return profiles
    
    async def _get_or_validate_provider(self, db: AsyncSession, provider_type: type, provider_data: dict) -> uuid.UUID:
        """Helper function to get provider ID by ID or name."""
        provider_id = provider_data.get('id')
        provider_name = provider_data.get('provider')

        if provider_id:
            stmt = select(provider_type).where(provider_type.id == provider_id)
            result = await db.execute(stmt)
            provider_obj = result.scalar_one_or_none()
            if not provider_obj or provider_obj.provider != provider_name:
                raise HTTPException(status_code=400, detail=f"Invalid {provider_type.__tablename__.replace('_', ' ')}: ID or name mismatch.")
            return provider_obj.id
        elif provider_name:
            stmt = select(provider_type).where(provider_type.provider == provider_name)
            result = await db.execute(stmt)
            provider_obj = result.scalar_one_or_none()
            if not provider_obj:
                raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not found.")
            return provider_obj.id
        else:
            raise HTTPException(status_code=400, detail=f"Missing ID or provider name for one of the providers.")

    async def create(self, db: AsyncSession, *, obj_in: AgentProfileCreate, owner_id: uuid.UUID) -> AgentProfileInDB:
        llm_provider_id = await self._get_or_validate_provider(db, LLMProvider, obj_in.llm_provider.model_dump())
        tts_provider_id = await self._get_or_validate_provider(db, TTSProvider, obj_in.tts_provider.model_dump())
        stt_provider_id = await self._get_or_validate_provider(db, STTProvider, obj_in.stt_provider.model_dump())

        await self._validate_options(db, llm_provider_id, tts_provider_id, stt_provider_id, obj_in)

        if obj_in.is_default:
            await db.execute(
                update(AgentProfile)
                .where(AgentProfile.owner_id == owner_id)
                .values(is_default=False)
            )

        # CHANGED: Convert options from Pydantic models to dicts before creating internal schema
        internal_data = obj_in.model_dump(exclude={"llm_provider", "tts_provider", "stt_provider"})
        internal_data["owner_id"] = owner_id
        internal_data["llm_provider_id"] = llm_provider_id
        internal_data["tts_provider_id"] = tts_provider_id
        internal_data["stt_provider_id"] = stt_provider_id

        internal_obj = AgentProfileCreateInternal(**internal_data)

        new_profile = await super().create(db=db, object=internal_obj)
        await db.refresh(new_profile, ["llm_provider", "tts_provider", "stt_provider"])
        return self._construct_profile(new_profile)

    async def _get_or_validate_provider_for_update(self, db: AsyncSession, provider_type: any, provider_data: Dict[str, Any], current_provider_id: uuid.UUID) -> uuid.UUID:
        """Helper to get a provider ID from a dictionary, falling back to the current ID if no new data is provided."""
        
        # Check if the provider field was sent at all
        if not provider_data:
            return current_provider_id
            
        provider_id = provider_data.get('id')
        provider_name = provider_data.get('provider')
        
        # If both ID and name are missing, return the current ID
        if not provider_id and not provider_name:
            return current_provider_id
        
        # If ID is provided, validate it
        if provider_id:
            stmt = select(provider_type).where(provider_type.id == provider_id)
            result = await db.execute(stmt)
            provider_obj = result.scalar_one_or_none()
            if not provider_obj or (provider_name and provider_obj.provider != provider_name):
                raise HTTPException(status_code=400, detail=f"Invalid {provider_type.__tablename__.replace('_', ' ')} ID or name mismatch.")
            return provider_obj.id
        
        # If only name is provided, find the ID
        if provider_name:
            stmt = select(provider_type).where(provider_type.provider == provider_name)
            result = await db.execute(stmt)
            provider_obj = result.scalar_one_or_none()
            if not provider_obj:
                raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not found.")
            return provider_obj.id
            
        return current_provider_id

    async def update(
        self, db: AsyncSession, *, id: uuid.UUID, obj_in: AgentProfileUpdate, owner_id: Optional[uuid.UUID] = None
    ) -> AgentProfileInDB:
        db_obj = await self.get(db=db, id=id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Agent profile not found")

        if owner_id is not None and db_obj.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        if obj_in.is_default:
            await db.execute(
                update(AgentProfile)
                .where(and_(
                    AgentProfile.owner_id == db_obj.owner_id,
                    AgentProfile.id != id
                ))
                .values(is_default=False)
            )

        # Convert incoming Pydantic model to a dictionary.
        # This is where nested models like TTSOptions are converted.
        update_data = obj_in.model_dump(exclude_unset=True)

        llm_provider_id = await self._get_or_validate_provider_for_update(db, LLMProvider, update_data.pop('llm_provider', {}), db_obj.llm_provider.id)
        tts_provider_id = await self._get_or_validate_provider_for_update(db, TTSProvider, update_data.pop('tts_provider', {}), db_obj.tts_provider.id)
        stt_provider_id = await self._get_or_validate_provider_for_update(db, STTProvider, update_data.pop('stt_provider', {}), db_obj.stt_provider.id)
        
        update_data['llm_provider_id'] = llm_provider_id
        update_data['tts_provider_id'] = tts_provider_id
        update_data['stt_provider_id'] = stt_provider_id

        await self._validate_options(db, llm_provider_id, tts_provider_id, stt_provider_id, obj_in)

        # Merge options logic
        if 'llm_options' in update_data:
            merged_options = db_obj.llm_options.copy()
            merged_options.update(update_data['llm_options'])
            update_data['llm_options'] = merged_options

        if 'tts_options' in update_data:
            merged_options = db_obj.tts_options.model_dump()
            merged_options.update(update_data['tts_options'])
            update_data['tts_options'] = merged_options

        if 'stt_options' in update_data:
            merged_options = db_obj.stt_options.model_dump()
            merged_options.update(update_data['stt_options'])
            update_data['stt_options'] = merged_options

        update_obj = AgentProfileUpdateInternal(**update_data)
        await super().update(db=db, id=id, object=update_obj)
        
        result = await db.execute(
            select(AgentProfile)
            .options(
                selectinload(AgentProfile.llm_provider),
                selectinload(AgentProfile.tts_provider),
                selectinload(AgentProfile.stt_provider)
            )
            .where(
                and_(
                    AgentProfile.id == id,
                    AgentProfile.owner_id == owner_id if owner_id else True
                )
            )
        )
        updated_profile = result.scalar_one_or_none()
        await db.commit()

        if updated_profile:
            return self._construct_profile(updated_profile)

        raise HTTPException(status_code=404, detail="Updated profile not found")

    async def get(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
        """Get an agent profile by ID, excluding soft-deleted profiles."""
        result = await db.execute(
            select(AgentProfile)
            .options(
                selectinload(AgentProfile.llm_provider),
                selectinload(AgentProfile.tts_provider),
                selectinload(AgentProfile.stt_provider)
            )
            .where(AgentProfile.id == id, AgentProfile.is_deleted == False)
        )
        profile = result.scalars().first()
        if profile:
            return self._construct_profile(profile)
        return None

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AgentProfileInDB]:
        """
        Soft-deletes an agent profile and its associated call logs.
        """
        # ... (rest of the method)
        # Step 1: Fetch the agent profile with its call logs and providers
        stmt = select(AgentProfile).options(
            selectinload(AgentProfile.call_logs),
            selectinload(AgentProfile.llm_provider),
            selectinload(AgentProfile.tts_provider),
            selectinload(AgentProfile.stt_provider)
        ).where(AgentProfile.id == id)
        result = await db.execute(stmt)
        profile_to_delete = result.scalar_one_or_none()

        if not profile_to_delete:
            return None

        # Step 2: Check if already soft-deleted
        if profile_to_delete.is_deleted:
            return None  # Or raise HTTPException(status_code=404, detail="Agent profile already deleted")

        # Step 3: Construct the response object before updating
        response_data = self._construct_profile(profile_to_delete)

        # Step 4: Soft-delete related call logs
        await db.execute(
            update(CallLog)  # Use CallLog model instead of "call_logs"
            .where(and_(CallLog.agent_id == id, CallLog.is_deleted == False))
            .values(is_deleted=True, updated_at=func.now())
        )

        # Step 5: Soft-delete the agent profile
        await db.execute(
            update(AgentProfile)
            .where(AgentProfile.id == id)
            .values(is_deleted=True, updated_at=func.now())
        )

        # Step 6: Commit changes
        await db.commit()

        # Step 7: Return the data of the agent that was soft-deleted
        return response_data


    def _construct_profile(self, item: any) -> AgentProfileInDB:
        """Helper to construct AgentProfileInDB from ORM."""
        if not hasattr(item, 'llm_provider') or not item.llm_provider:
            raise HTTPException(status_code=500, detail="LLM provider not loaded for profile")
        if not hasattr(item, 'tts_provider') or not item.tts_provider:
            raise HTTPException(status_code=500, detail="TTS provider not loaded for profile")
        if not hasattr(item, 'stt_provider') or not item.stt_provider:
            raise HTTPException(status_code=500, detail="STT provider not loaded for profile")
        
        # Exclude relationship attributes to avoid duplicate keyword arguments
        item_dict = item.__dict__.copy()
        item_dict.pop('llm_provider', None)
        item_dict.pop('tts_provider', None)
        item_dict.pop('stt_provider', None)
        item_dict.pop('_sa_instance_state', None)  # Remove SQLAlchemy internal state
        
        return AgentProfileInDB(
            **item_dict,
            llm_provider=ProviderBase(id=item.llm_provider.id, provider=item.llm_provider.provider),
            tts_provider=ProviderBase(id=item.tts_provider.id, provider=item.tts_provider.provider),
            stt_provider=ProviderBase(id=item.stt_provider.id, provider=item.stt_provider.provider),
        )

    async def _validate_options(
        self, db: AsyncSession, llm_provider_id: uuid.UUID, tts_provider_id: uuid.UUID, stt_provider_id: uuid.UUID, obj_in: AgentProfileCreate | AgentProfileUpdate
    ) -> None:
        """Validate options against provider models, voices, and languages."""
        llm_provider = (await db.execute(select(LLMProvider).where(LLMProvider.id == llm_provider_id))).scalar_one_or_none()
        tts_provider = (await db.execute(select(TTSProvider).where(TTSProvider.id == tts_provider_id))).scalar_one_or_none()
        stt_provider = (await db.execute(select(STTProvider).where(STTProvider.id == stt_provider_id))).scalar_one_or_none()
        
        if hasattr(obj_in, 'llm_options') and obj_in.llm_options and 'model' in obj_in.llm_options:
            if not llm_provider or obj_in.llm_options['model'] not in llm_provider.models:
                raise HTTPException(status_code=400, detail=f"Invalid model in llm_options: {obj_in.llm_options['model']}")

        # FIXED: Access attributes directly from the Pydantic model object
        if hasattr(obj_in, 'tts_options') and obj_in.tts_options:
            tts_opts = obj_in.tts_options
            
            if tts_opts.voice:
                if not tts_provider or not any(v['id'] == tts_opts.voice for v in tts_provider.voices):
                    raise HTTPException(status_code=400, detail=f"Invalid voice in tts_options: {tts_opts.voice}")

            if tts_opts.model and tts_opts.language:
                if not tts_provider:
                    raise HTTPException(status_code=400, detail="TTS provider not found for validation.")
                
                model_found = False
                for m in tts_provider.models:
                    if m['model'] == tts_opts.model:
                        model_found = True
                        if tts_opts.language not in m.get('languages', []):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Language '{tts_opts.language}' not supported by TTS model '{tts_opts.model}'"
                            )
                        break
                if not model_found:
                    raise HTTPException(status_code=400, detail=f"Invalid model in tts_options: {tts_opts.model}")

        # FIXED: Access attributes directly from the Pydantic model object
        if hasattr(obj_in, 'stt_options') and obj_in.stt_options:
            stt_opts = obj_in.stt_options
            
            if stt_opts.model and stt_opts.language:
                if not stt_provider:
                    raise HTTPException(status_code=400, detail="STT provider not found for validation.")

                model_found = False
                for m in stt_provider.models:
                    if m['model'] == stt_opts.model:
                        model_found = True
                        if stt_opts.language not in m.get('languages', []):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Language '{stt_opts.language}' not supported by STT model '{stt_opts.model}'"
                            )
                        break
                if not model_found:
                    raise HTTPException(status_code=400, detail=f"Invalid model in stt_options: {stt_opts.model}")

crud_agent_profiles = CRUDAgentProfileExtended(AgentProfile)