import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base



class ClosetItem(Base):
    __tablename__ = "closet_items"

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
    # File reference (served via /files/{closet_item_id}/{filename})
    image_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


    # Core classification
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    primary_color: Mapped[str] = mapped_column(String(50), nullable=False)
    secondary_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # User-entered attributes
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fabric: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Arrays for filtering (Postgres)
    seasons: Mapped[List[str]] = mapped_column(
        ARRAY(String(20)),
        nullable=False,
        default=list
    )

    tags: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        default=list
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing + lifecycle
    processing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="processing"  # processing | ready | failed
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
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

    # relationship back to User (optional)
    user = relationship("User", backref="closet_items")
