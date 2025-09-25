from typing import List, Optional, Dict, Any
import uuid
from fastapi import HTTPException
from sqlalchemy import and_, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
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
)

# Connection CRUD
from ..models.connections import Connection
from ..schemas.connections import (
    ConnectionCreate,
    ConnectionCreateInternal,
    ConnectionInDB,
    ProviderBase,
)

class CRUDConnection(FastCRUD[
    Connection,
    ConnectionCreateInternal,
    ConnectionCreateInternal,
    ConnectionCreateInternal,
    ConnectionCreateInternal,
    ConnectionInDB
]):
    async def get_by_room_id(self, db: AsyncSession, *, room_id: str | uuid.UUID) -> Optional[ConnectionInDB]:
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)

        # ... (This method remains unchanged)
        result = await db.execute(
            select(Connection)
            .options(
                selectinload(Connection.llm_provider),
                selectinload(Connection.tts_provider),
                selectinload(Connection.stt_provider)
            )
            .where(Connection.room_id == room_id)
        )
        connection = result.scalars().first()
        if connection:
            return self._construct_connection(connection)
        return None

    async def create_connection(
        self,
        db: AsyncSession,
        *,
        room_id: str | uuid.UUID,
        agent_id: uuid.UUID,
        owner_id: uuid.UUID,
        call_id: Optional[str] = None  # <-- Parameter added
    ) -> ConnectionInDB:
        """Create a new connection by fetching agent data and all related documents."""

        print(f"Creating connection for room_id in crud_connections.py Ahtasham: {room_id}, agent_id: {agent_id}, owner_id: {owner_id}, call_id: {call_id}")

        # 1. Fetch the agent profile with necessary relationships
        agent_profile_query = select(AgentProfile).options(
            selectinload(AgentProfile.llm_provider),
            selectinload(AgentProfile.tts_provider),
            selectinload(AgentProfile.stt_provider),
            selectinload(AgentProfile.knowledge_bases).joinedload(KnowledgeBase.documents)
        ).where(AgentProfile.id == agent_id)

        result = await db.execute(agent_profile_query)
        agent_profile = result.scalars().first()

        if not agent_profile:
            raise HTTPException(status_code=404, detail="Agent profile not found")

        if agent_profile.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Not enough permissions to use this agent profile")

        # 2. Prepare the data for the database object.
        knowledge_bases_with_docs = [
            {
                "id": str(kb.id),
                "name": kb.name,
                "description": kb.description,
                "qdrant_collection": kb.qdrant_collection,
                "owner_id": str(kb.owner_id),
                "documents": [
                    {
                        "id": str(doc.id),
                        "filename": doc.filename,
                        "content_type": doc.content_type,
                        "content": doc.content,
                        "chunk_count": doc.chunk_count,
                        "created_at": doc.created_at.isoformat(),
                        "updated_at": doc.updated_at.isoformat(),
                        "knowledge_base_id": str(kb.id)
                    } for doc in kb.documents
                ]
            } for kb in agent_profile.knowledge_bases
        ]

        connection_data = {
            "room_id": room_id,
            "call_id": call_id,  # <-- Field added here
            "owner_id": owner_id,
            "name": agent_profile.name,
            "description": agent_profile.description,
            "system_prompt": agent_profile.system_prompt,
            "greeting": agent_profile.greeting,
            "llm_provider_id": agent_profile.llm_provider.id,
            "tts_provider_id": agent_profile.tts_provider.id,
            "stt_provider_id": agent_profile.stt_provider.id,
            "llm_options": agent_profile.llm_options,
            "tts_options": agent_profile.tts_options,
            "stt_options": agent_profile.stt_options,
            "profile_options": agent_profile.profile_options,
            "allow_interruptions": agent_profile.allow_interruptions,
            "interrupt_speech_duration": agent_profile.interrupt_speech_duration,
            "interrupt_min_words": agent_profile.interrupt_min_words,
            "min_endpointing_delay": agent_profile.min_endpointing_delay,
            "max_endpointing_delay": agent_profile.max_endpointing_delay,
            "active": agent_profile.active,
            "is_default": agent_profile.is_default,
            "is_record": agent_profile.is_record, # <-- Field added
            "max_nested_function_calls": agent_profile.max_nested_function_calls,
            "knowledge_bases_data": knowledge_bases_with_docs
        }

        # 3. Create the SQLAlchemy object directly and link the relationship.
        # THIS IS THE CORRECT AND FINAL WORKAROUND.
        new_connection = Connection(**connection_data)
        new_connection.agent_profile = agent_profile

        # 4. Add the object to the session and commit.
        db.add(new_connection)
        await db.commit()
        await db.refresh(new_connection)

        # 5. Return the final, validated object
        return self._construct_connection(new_connection)

    def _construct_connection(self, item: Any) -> ConnectionInDB:
        """
        Helper to construct ConnectionInDB from ORM,
        including nested knowledge base data from the JSONB field.
        """
        # Ensure provider relationships are loaded
        if not hasattr(item, 'llm_provider') or not item.llm_provider:
            raise HTTPException(status_code=500, detail="LLM provider not loaded for connection")
        if not hasattr(item, 'tts_provider') or not item.tts_provider:
            raise HTTPException(status_code=500, detail="TTS provider not loaded for connection")
        if not hasattr(item, 'stt_provider') or not item.stt_provider:
            raise HTTPException(status_code=500, detail="STT provider not loaded for connection")
        
        # Create a dictionary from the ORM object, excluding SQLAlchemy internal state
        item_dict = {
            c.name: getattr(item, c.name) 
            for c in item.__table__.columns
        }
        
        knowledge_bases_data = []
        if item.knowledge_bases_data:
            for kb_data in item.knowledge_bases_data:
                documents_data = []
                if kb_data.get('documents'):
                    for doc_data in kb_data['documents']:
                        # CORRECTED: Add the knowledge_base_id here before validation
                        doc_data['knowledge_base_id'] = kb_data['id'] 
                        documents_data.append(DocumentWithContentRead(**doc_data))
                
                kb_data['documents'] = documents_data
                knowledge_bases_data.append(KnowledgeBaseWithDocsRead(**kb_data))
        
        item_dict['knowledge_bases'] = knowledge_bases_data
        
        # Return the final Pydantic model
        return ConnectionInDB(
            **item_dict,
            llm_provider=ProviderBase(id=item.llm_provider.id, provider=item.llm_provider.provider),
            tts_provider=ProviderBase(id=item.tts_provider.id, provider=item.tts_provider.provider),
            stt_provider=ProviderBase(id=item.stt_provider.id, provider=item.stt_provider.provider),
        )

    async def _validate_connection_options(
        self, 
        db: AsyncSession, 
        llm_provider_id: uuid.UUID, 
        tts_provider_id: uuid.UUID, 
        stt_provider_id: uuid.UUID, 
        obj_in: ConnectionCreate
    ) -> None:
        """Validate llm_options, tts_options, and stt_options against provider models and voices."""
        llm_provider = (await db.execute(select(LLMProvider).where(LLMProvider.id == llm_provider_id))).scalar_one_or_none()
        tts_provider = (await db.execute(select(TTSProvider).where(TTSProvider.id == tts_provider_id))).scalar_one_or_none()
        stt_provider = (await db.execute(select(STTProvider).where(STTProvider.id == stt_provider_id))).scalar_one_or_none()

        if hasattr(obj_in, 'llm_options') and obj_in.llm_options and 'model' in obj_in.llm_options:
            if not llm_provider or obj_in.llm_options['model'] not in llm_provider.models:
                raise HTTPException(status_code=400, detail=f"Invalid model in llm_options: {obj_in.llm_options['model']}")

        if hasattr(obj_in, 'tts_options') and obj_in.tts_options:
            if 'model' in obj_in.tts_options:
                if not tts_provider or not any(m['model'] == obj_in.tts_options['model'] for m in tts_provider.models):
                    raise HTTPException(status_code=400, detail=f"Invalid model in tts_options: {obj_in.tts_options['model']}")
            if 'voice' in obj_in.tts_options:
                if not tts_provider or not any(v['id'] == obj_in.tts_options['voice'] for v in tts_provider.voices):
                    raise HTTPException(status_code=400, detail=f"Invalid voice in tts_options: {obj_in.tts_options['voice']}")

        if hasattr(obj_in, 'stt_options') and obj_in.stt_options and 'model' in obj_in.stt_options:
            if not stt_provider or not any(m['model'] == obj_in.stt_options['model'] for m in stt_provider.models):
                raise HTTPException(status_code=400, detail=f"Invalid model in stt_options: {obj_in.stt_options['model']}")

# Create a singleton CRUD instance for connections
crud_connections = CRUDConnection(Connection)
