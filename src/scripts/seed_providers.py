import asyncio
import os
import sys
from datetime import datetime, timezone  # Added timezone

# Add the parent directory (src) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.agent_profile import LLMProvider, TTSProvider, STTProvider
from app.core.db.database import Base
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async def seed_providers():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/livekit_agents", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Current time (offset-naive UTC)
        now = datetime.now(timezone.utc)  # Fixed with proper import
        # now = datetime.now(timezone.utc).replace(tzinfo=None)  # Fixed with proper import

        # LLM Providers
        llm_providers = [
            LLMProvider(),
            LLMProvider(),
            LLMProvider()
        ]
        llm_providers[0].provider = "OpenAI"
        llm_providers[0].models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3", "o4-mini"]
        llm_providers[0].created_at = now
        llm_providers[0].updated_at = now
        llm_providers[1].provider = "Anthropic"
        llm_providers[1].models = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        llm_providers[1].created_at = now
        llm_providers[1].updated_at = now
        llm_providers[2].provider = "Google"
        llm_providers[2].models = ["gemini-pro", "gemini-1.5-flash"]
        llm_providers[2].created_at = now
        llm_providers[2].updated_at = now
        session.add_all(llm_providers)

        # TTS Providers
        tts_providers = [
            TTSProvider(),
            TTSProvider(),
            TTSProvider(),
            TTSProvider(),
            TTSProvider()
        ]
        tts_providers[0].provider = "OpenAI"
        tts_providers[0].models = [
            {"model": "tts-1", "languages": ["en", "es", "fr", "de", "it"]},
            {"model": "tts-1-hd", "languages": ["en", "es", "fr", "de", "it"]}
        ]
        tts_providers[0].voices = [
            {"id": "alloy", "age": "Adult", "name": "Alloy", "accent": "US", "gender": "neutral", "voice_url": None},
            {"id": "nova", "age": "Adult", "name": "Nova", "accent": "US", "gender": "female", "voice_url": None}
        ]
        tts_providers[0].created_at = now
        tts_providers[0].updated_at = now
        tts_providers[1].provider = "Google"
        tts_providers[1].models = [
            {"model": "neural2", "languages": ["en-US", "es-ES", "fr-FR"]},
            {"model": "standard", "languages": ["en-US", "es-ES"]}
        ]
        tts_providers[1].voices = [
            {"id": "en-US-Neural2-F", "age": "Adult", "name": "Female Neural", "accent": "US", "gender": "female", "voice_url": None},
            {"id": "en-US-Standard-B", "age": "Adult", "name": "Male Standard", "accent": "US", "gender": "male", "voice_url": None}
        ]
        tts_providers[1].created_at = now
        tts_providers[1].updated_at = now
        tts_providers[2].provider = "ElevenLabs"
        tts_providers[2].models = [
            {"model": "multilingual-v2", "languages": ["en", "es", "fr"]},
            {"model": "turbo-v2", "languages": ["en"]}
        ]
        tts_providers[2].voices = [
            {"id": str(uuid.uuid4()), "age": "Adult", "name": "Anika", "accent": "US", "gender": "female", "voice_url": None}
        ]
        tts_providers[2].created_at = now
        tts_providers[2].updated_at = now
        tts_providers[3].provider = "Cartesia"
        tts_providers[3].models = [
            {"model": "sonic-2", "languages": ["en", "es", "fr"]},
            {"model": "sonic-turbo", "languages": ["en"]}
        ]
        tts_providers[3].voices = [
            {"id": str(uuid.uuid4()), "age": "Adult", "name": "Brooke", "accent": "US", "gender": "female", "voice_url": None}
        ]
        tts_providers[3].created_at = now
        tts_providers[3].updated_at = now
        tts_providers[4].provider = "Uplift"
        tts_providers[4].models = [
            {"model": "uplift-1", "languages": ["en", "es"]}
        ]
        tts_providers[4].voices = [
            {"id": str(uuid.uuid4()), "age": "Adult", "name": "Default", "accent": "US", "gender": "neutral", "voice_url": None}
        ]
        tts_providers[4].created_at = now
        tts_providers[4].updated_at = now
        session.add_all(tts_providers)

        # STT Providers
        stt_providers = [
            STTProvider(),
            STTProvider()
        ]
        stt_providers[0].provider = "Deepgram"
        stt_providers[0].models = [
            {"model": "nova-3", "languages": ["en", "en-US", "multi"]},
            {"model": "nova-2", "languages": ["en", "es", "fr"]}
        ]
        stt_providers[0].created_at = now
        stt_providers[0].updated_at = now
        stt_providers[1].provider = "Google"
        stt_providers[1].models = [
            {"model": "latest_long", "languages": ["en-US", "es-ES"]},
            {"model": "chirp2", "languages": ["en-US"]}
        ]
        stt_providers[1].created_at = now
        stt_providers[1].updated_at = now
        session.add_all(stt_providers)

        await session.commit()
        print("Seeded providers successfully.")

if __name__ == "__main__":
    asyncio.run(seed_providers())