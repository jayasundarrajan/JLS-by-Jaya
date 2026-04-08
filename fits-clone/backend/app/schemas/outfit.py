from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class OutfitCreate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None  # manual | ai_saved


class OutfitOut(BaseModel):
    id: UUID
    user_id: UUID
    name: Optional[str]
    notes: Optional[str]
    source: Optional[str]
    is_archived: bool

    class Config:
        from_attributes = True


class OutfitItemCreate(BaseModel):
    closet_item_id: UUID

    # Optional: if omitted, backend will default to center (0.5, 0.5)
    x: Optional[float] = Field(None, ge=0.0, le=1.0)
    y: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Optional: backend defaults if omitted
    scale: Optional[float] = Field(None, gt=0.0)
    rotation: Optional[float] = None
    z_index: Optional[int] = None


class OutfitItemBulkPatch(BaseModel):
    id: UUID
    x: Optional[float] = Field(None, ge=0.0, le=1.0)
    y: Optional[float] = Field(None, ge=0.0, le=1.0)
    scale: Optional[float] = Field(None, gt=0.0)
    rotation: Optional[float] = None
    z_index: Optional[int] = None


class OutfitItemsBulkUpdate(BaseModel):
    items: List[OutfitItemBulkPatch]



class OutfitItemPatch(BaseModel):
    x: Optional[float] = Field(None, ge=0.0, le=1.0)
    y: Optional[float] = Field(None, ge=0.0, le=1.0)
    scale: Optional[float] = Field(None, gt=0.0)
    rotation: Optional[float] = None
    z_index: Optional[int] = None


class OutfitItemOut(BaseModel):
    id: UUID
    outfit_id: UUID
    closet_item_id: UUID
    x: float
    y: float
    scale: float
    rotation: float
    z_index: int

    class Config:
        from_attributes = True

class OutfitItemRenderOut(OutfitItemOut):
    cutout_url: Optional[str] = None
    original_url: Optional[str] = None

class OutfitDetailOut(OutfitOut):
    items: List[OutfitItemRenderOut] = []

