import uuid
from datetime import datetime
from typing import Optional, Any, Dict

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class StylistRequest(Base):
    __tablename__ = "stylist_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    occasion: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    style_vibe: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    constraints_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Weather snapshot from a weather API (auto, with manual fallback)
    weather_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued"  # queued | running | completed | failed
    )

    # Optional link to the background Job that produced the results
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    model: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    prompt_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship("User", backref="stylist_requests")
    job = relationship("Job", backref="stylist_requests")
