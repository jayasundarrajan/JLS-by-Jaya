from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class PasswordCredentials(Base):
    __tablename__ = "password_credentials"

    # user_id is both PK and FK → enforces 1:1 relationship
    user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("users.id", ondelete="CASCADE"),
    primary_key=True
)

    password_hash: Mapped[str] = mapped_column(
        nullable=False
    )

    password_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # optional relationship back to User
    user = relationship("User", backref="password_credentials")
