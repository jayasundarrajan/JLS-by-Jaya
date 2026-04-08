import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    outfit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outfits.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    closet_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Canvas placement (normalized 0..1)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)

    # Transform
    scale: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    rotation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # degrees

    # Layering
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

    outfit = relationship("Outfit", backref="outfit_items")
    closet_item = relationship("ClosetItem")
