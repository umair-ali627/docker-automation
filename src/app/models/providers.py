from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, ForeignKey, JSON as JSONB, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.db.database import Base
import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

class LLMProvider(Base):
    __tablename__ = "llm_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
    provider = Column(String, unique=True, index=True)  # Added to match schema
    models = Column(JSONB, default=list)  # List of strings, e.g., ["gpt-4o", ...]

class STTProvider(Base):
    __tablename__ = "stt_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
    provider = Column(String, unique=True, index=True)  # Added to match schema
    models = Column(JSONB, default=list)

class TTSProvider(Base):
    __tablename__ = "tts_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=func.now(), onupdate=func.now())
    provider = Column(String, unique=True, index=True)  # Added to match schema
    models = Column(JSONB, default=list)  # List of dicts, e.g., [{"model": "sonic-2", "languages": ["en", ...]}]
    voices = Column(JSONB, default=list)  # List of dicts, e.g., [{"id": "...", "name": "Brooke", ...}]

