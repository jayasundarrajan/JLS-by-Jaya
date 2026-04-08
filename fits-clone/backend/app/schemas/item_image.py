from pydantic import BaseModel
from uuid import UUID

class ItemImageOut(BaseModel):
    id: UUID
    closet_item_id: UUID
    image_role: str
    storage_provider: str
    storage_key: str
    public_url: str | None
    width: int | None
    height: int | None
    mime_type: str | None
    source_type: str
    source_url: str | None
    source_provider: str | None
    status: str
    checksum: str | None

    class Config:
        from_attributes = True
