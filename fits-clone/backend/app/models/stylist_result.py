import uuid
from datetime import datetime
from typing import Optional, Any, Dict

from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class StylistResult(Base):
    __tablename__ = "stylist_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    stylist_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stylist_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False  # 1..3
    )

    # References ClosetItem IDs, plus optional notes/slots
    outfit_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False
    )

    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structure now, logic later
    swap_suggestions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True
    )

    # When user saves this suggestion into a real Outfit
    saved_outfit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outfits.id", ondelete="SET NULL"),
        nullable=True,
        index=True
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

    stylist_request = relationship("StylistRequest", backref="results")
    saved_outfit = relationship("Outfit", backref="saved_from_stylist_results")
