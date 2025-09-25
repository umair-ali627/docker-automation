import uuid as uuid_pkg
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..core.db.database import Base


class User(Base):
    __tablename__ = "user"

    # Required fields first
    username: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    
    # Change id to UUID type
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid_pkg.uuid4
    )
    profile_image_url: Mapped[str] = mapped_column(String, default="https://profileimageurl.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    tier_id: Mapped[int | None] = mapped_column(ForeignKey("tier.id"), index=True, default=None, init=False)

    agent_profiles = relationship("AgentProfile", back_populates="owner")
    knowledge_bases = relationship("KnowledgeBase", back_populates="owner")
    sip_trunks = relationship("SIPTrunk", back_populates="owner")
    function_tools = relationship("FunctionTool", back_populates="owner")
