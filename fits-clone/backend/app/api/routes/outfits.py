import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.outfit import Outfit
from app.models.outfit_item import OutfitItem
from app.models.closet_item import ClosetItem
from app.models.item_image import ItemImage
from app.schemas.outfit import (
    OutfitCreate,
    OutfitOut,
    OutfitDetailOut,
    OutfitItemCreate,
    OutfitItemOut,
    OutfitItemPatch,
    OutfitItemsBulkUpdate,
)

router = APIRouter()


def build_abs_url(request: Request, public_url: str | None) -> str | None:
    if not public_url:
        return None
    return str(request.base_url).rstrip("/") + public_url


@router.put("/{outfit_id}/items/bulk", response_model=list[OutfitItemOut])
def bulk_update_outfit_items(
    outfit_id: str,
    payload: OutfitItemsBulkUpdate,
    db: Session = Depends(get_db),
):
    try:
        outfit_uuid = uuid.UUID(outfit_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid outfit_id")

    outfit = db.query(Outfit).filter(Outfit.id == outfit_uuid).first()
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    existing_items = (
        db.query(OutfitItem)
        .filter(OutfitItem.outfit_id == outfit.id)
        .all()
    )
    by_id = {str(oi.id): oi for oi in existing_items}

    updated: list[OutfitItem] = []

    for patch in payload.items:
        oi = by_id.get(str(patch.id))
        if not oi:
            raise HTTPException(status_code=404, detail=f"OutfitItem not found: {patch.id}")

        if patch.x is not None:
            oi.x = patch.x
        if patch.y is not None:
            oi.y = patch.y
        if patch.scale is not None:
            oi.scale = patch.scale
        if patch.rotation is not None:
            oi.rotation = patch.rotation
        if patch.z_index is not None:
            oi.z_index = patch.z_index

        updated.append(oi)

    db.commit()

    for oi in updated:
        db.refresh(oi)

    updated.sort(key=lambda o: (o.z_index, o.created_at))
    return updated


@router.post("", response_model=OutfitOut)
def create_outfit(
    user_id: str,
    payload: OutfitCreate,
    db: Session = Depends(get_db),
):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    outfit = Outfit(
        user_id=user_uuid,
        name=payload.name,
        notes=payload.notes,
        source=payload.source,
        is_archived=False,
    )
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    return outfit


@router.get("", response_model=list[OutfitOut])
def list_outfits(
    user_id: str,
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    q = db.query(Outfit).filter(Outfit.user_id == user_uuid)
    if not include_archived:
        q = q.filter(Outfit.is_archived == False)  # noqa: E712

    return q.order_by(Outfit.created_at.desc()).all()


@router.get("/{outfit_id}", response_model=OutfitDetailOut)
def get_outfit_detail(outfit_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        outfit_uuid = uuid.UUID(outfit_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid outfit_id")

    outfit = db.query(Outfit).filter(Outfit.id == outfit_uuid).first()
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    items = (
        db.query(OutfitItem)
        .filter(OutfitItem.outfit_id == outfit.id)
        .order_by(OutfitItem.z_index.asc(), OutfitItem.created_at.asc())
        .all()
    )

    render_items = []
    for oi in items:
        cutout = (
            db.query(ItemImage)
            .filter(
                ItemImage.closet_item_id == oi.closet_item_id,
                ItemImage.image_role == "cutout",
            )
            .order_by(ItemImage.created_at.desc())
            .first()
        )
        original = (
            db.query(ItemImage)
            .filter(
                ItemImage.closet_item_id == oi.closet_item_id,
                ItemImage.image_role == "original",
            )
            .order_by(ItemImage.created_at.desc())
            .first()
        )

        render_items.append(
            {
                "id": oi.id,
                "outfit_id": oi.outfit_id,
                "closet_item_id": oi.closet_item_id,
                "x": oi.x,
                "y": oi.y,
                "scale": oi.scale,
                "rotation": oi.rotation,
                "z_index": oi.z_index,
                "cutout_url": build_abs_url(request, cutout.public_url if cutout else None),
                "original_url": build_abs_url(request, original.public_url if original else None),
            }
        )

    return {
        "id": outfit.id,
        "user_id": outfit.user_id,
        "name": outfit.name,
        "notes": outfit.notes,
        "source": outfit.source,
        "is_archived": outfit.is_archived,
        "items": render_items,
    }


@router.post("/{outfit_id}/items", response_model=OutfitItemOut)
def add_outfit_item(outfit_id: str, payload: OutfitItemCreate, db: Session = Depends(get_db)):
    try:
        outfit_uuid = uuid.UUID(outfit_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid outfit_id")

    outfit = db.query(Outfit).filter(Outfit.id == outfit_uuid).first()
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    closet_item = db.query(ClosetItem).filter(ClosetItem.id == payload.closet_item_id).first()
    if not closet_item:
        raise HTTPException(status_code=404, detail="ClosetItem not found")

    if closet_item.user_id != outfit.user_id:
        raise HTTPException(status_code=403, detail="ClosetItem does not belong to this user")

    x = payload.x if payload.x is not None else 0.5
    y = payload.y if payload.y is not None else 0.5
    scale = payload.scale if payload.scale is not None else 1.0
    rotation = payload.rotation if payload.rotation is not None else 0.0

    if payload.z_index is None:
        max_z = (
            db.query(OutfitItem.z_index)
            .filter(OutfitItem.outfit_id == outfit.id)
            .order_by(OutfitItem.z_index.desc())
            .first()
        )
        z_index = (max_z[0] + 1) if max_z else 0
    else:
        z_index = payload.z_index

    oi = OutfitItem(
        outfit_id=outfit.id,
        closet_item_id=payload.closet_item_id,
        x=x,
        y=y,
        scale=scale,
        rotation=rotation,
        z_index=z_index,
    )

    db.add(oi)
    db.commit()
    db.refresh(oi)
    return oi


@router.patch("/{outfit_id}/items/{outfit_item_id}", response_model=OutfitItemOut)
def patch_outfit_item(
    outfit_id: str,
    outfit_item_id: str,
    payload: OutfitItemPatch,
    db: Session = Depends(get_db),
):
    try:
        outfit_uuid = uuid.UUID(outfit_id)
        oi_uuid = uuid.UUID(outfit_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id")

    oi = (
        db.query(OutfitItem)
        .filter(OutfitItem.id == oi_uuid, OutfitItem.outfit_id == outfit_uuid)
        .first()
    )
    if not oi:
        raise HTTPException(status_code=404, detail="OutfitItem not found")

    if payload.x is not None:
        oi.x = payload.x
    if payload.y is not None:
        oi.y = payload.y
    if payload.scale is not None:
        oi.scale = payload.scale
    if payload.rotation is not None:
        oi.rotation = payload.rotation
    if payload.z_index is not None:
        oi.z_index = payload.z_index

    db.commit()
    db.refresh(oi)
    return oi


@router.delete("/{outfit_id}/items/{outfit_item_id}")
def delete_outfit_item(outfit_id: str, outfit_item_id: str, db: Session = Depends(get_db)):
    try:
        outfit_uuid = uuid.UUID(outfit_id)
        oi_uuid = uuid.UUID(outfit_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id")

    oi = (
        db.query(OutfitItem)
        .filter(OutfitItem.id == oi_uuid, OutfitItem.outfit_id == outfit_uuid)
        .first()
    )
    if not oi:
        raise HTTPException(status_code=404, detail="OutfitItem not found")

    db.delete(oi)
    db.commit()
    return {"status": "deleted"}
