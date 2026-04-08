from pydantic import BaseModel
from typing import List
from uuid import UUID


class ClosetItemCreate(BaseModel):
    category: str
    primary_color: str
    secondary_color: str | None = None
    size: str | None = None
    brand: str | None = None
    fabric: str | None = None
    pattern: str | None = None
    seasons: List[str] = []
    tags: List[str] = []
    notes: str | None = None


class ClosetItemOut(BaseModel):
    id: UUID
    user_id: UUID
    category: str
    primary_color: str
    secondary_color: str | None
    size: str | None
    brand: str | None
    fabric: str | None
    pattern: str | None
    seasons: List[str]
    tags: List[str]
    notes: str | None
    processing_status: str
    is_archived: bool

    # ✅ NEW (Option B)
    image_path: str | None = None
    image_url: str | None = None

    class Config:
        from_attributes = True
