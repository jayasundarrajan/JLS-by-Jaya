import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.closet_item import ClosetItem
from app.schemas.closet_item import ClosetItemCreate, ClosetItemOut
from sqlalchemy import or_, exists, select
from app.models.item_image import ItemImage

router = APIRouter()


@router.post("", response_model=ClosetItemOut)
def create_closet_item(
    user_id: str,
    payload: ClosetItemCreate,
    db: Session = Depends(get_db)
):
    # (temporary) accept user_id as a query param until auth is built
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    item = ClosetItem(
        user_id=user_uuid,
        category=payload.category,
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        size=payload.size,
        brand=payload.brand,
        fabric=payload.fabric,
        pattern=payload.pattern,
        seasons=payload.seasons,
        tags=payload.tags,
        notes=payload.notes,
        processing_status="ready",  # background removal later
        is_archived=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ClosetItemOut])
def list_closet_items(
    user_id: str,
    include_archived: bool = Query(False),

    # ---- filters ----
    category: str | None = Query(None),
    primary_color: str | None = Query(None),
    season: str | None = Query(None),
    tag: str | None = Query(None),
    search: str | None = Query(None),
    has_cutout: bool | None = Query(None),

    request: Request = None,
    db: Session = Depends(get_db),
):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    q = db.query(ClosetItem).filter(ClosetItem.user_id == user_uuid)

    if not include_archived:
        q = q.filter(ClosetItem.is_archived == False)  # noqa: E712

    if category:
        q = q.filter(ClosetItem.category.ilike(category))

    if primary_color:
        q = q.filter(ClosetItem.primary_color.ilike(primary_color))

    # seasons/tags are Postgres ARRAY columns; `.any()` maps to SQL = ANY(array)
    if season:
        q = q.filter(ClosetItem.seasons.any(season))

    if tag:
        q = q.filter(ClosetItem.tags.any(tag))

    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            or_(
                ClosetItem.brand.ilike(like),
                ClosetItem.notes.ilike(like),
                ClosetItem.pattern.ilike(like),
                ClosetItem.category.ilike(like),
                ClosetItem.primary_color.ilike(like),
                ClosetItem.secondary_color.ilike(like),
            )
        )

    # has_cutout = true => only items with at least one ready cutout image
    if has_cutout is True:
        cutout_exists = exists(
            select(1).where(
                (ItemImage.closet_item_id == ClosetItem.id)
                & (ItemImage.image_role == "cutout")
                & (ItemImage.status == "ready")
            )
        )
        q = q.filter(cutout_exists)

    # has_cutout = false => only items with NO ready cutout
    if has_cutout is False:
        cutout_exists = exists(
            select(1).where(
                (ItemImage.closet_item_id == ClosetItem.id)
                & (ItemImage.image_role == "cutout")
                & (ItemImage.status == "ready")
            )
        )
        q = q.filter(~cutout_exists)

    items = q.order_by(ClosetItem.created_at.desc()).all()

    base = str(request.base_url).rstrip("/") if request else ""
    out: list[ClosetItemOut] = []
    for item in items:
        dto = ClosetItemOut.model_validate(item, from_attributes=True)
        if getattr(dto, "image_path", None) and base:
            dto.image_url = f"{base}{dto.image_path}"
        out.append(dto)

    return out

