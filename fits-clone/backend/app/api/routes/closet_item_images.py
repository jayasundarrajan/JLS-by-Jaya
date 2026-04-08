import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.closet_item import ClosetItem
from app.models.item_image import ItemImage
from app.schemas.item_image import ItemImageOut

router = APIRouter()


@router.get("/closet-items/{closet_item_id}/images", response_model=list[ItemImageOut])
def list_closet_item_images(
    closet_item_id: str,
    db: Session = Depends(get_db),
):
    try:
        closet_uuid = uuid.UUID(closet_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid closet_item_id")

    item = db.query(ClosetItem).filter(ClosetItem.id == closet_uuid).first()
    if not item:
        raise HTTPException(status_code=404, detail="ClosetItem not found")

    latest_cutout = (
        db.query(ItemImage)
        .filter(
            ItemImage.closet_item_id == closet_uuid,
            ItemImage.image_role == "cutout",
        )
        .order_by(ItemImage.created_at.desc())
        .first()
    )

    latest_original = (
        db.query(ItemImage)
        .filter(
            ItemImage.closet_item_id == closet_uuid,
            ItemImage.image_role == "original",
        )
        .order_by(ItemImage.created_at.desc())
        .first()
    )

    images = []
    if latest_cutout:
        images.append(latest_cutout)
    if latest_original:
        images.append(latest_original)

    return images
