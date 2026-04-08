import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ItemImage(Base):
    __tablename__ = "item_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    closet_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # What kind of image
    image_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False  # original | cutout
    )

    # Storage
    storage_provider: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g. local-dev, r2, s3
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    public_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Source attribution
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False  # photo | file_upload | web
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Processing status for the asset itself
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ready"  # processing | ready | failed
    )

    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

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

    closet_item = relationship("ClosetItem", backref="images")
