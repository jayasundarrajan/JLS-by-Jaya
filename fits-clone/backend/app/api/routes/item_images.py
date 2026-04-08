import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.closet_item import ClosetItem
from app.models.item_image import ItemImage
from app.models.job import Job
from app.schemas.item_image import ItemImageOut

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")


@router.post("/upload", response_model=ItemImageOut)
def upload_item_image(
    closet_item_id: str = Form(...),
    source_type: str = Form("photo"),         # photo | file_upload | web
    source_url: str | None = Form(None),
    source_provider: str | None = Form(None), # e.g. pinterest, google
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate UUID
    try:
        closet_uuid = uuid.UUID(closet_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid closet_item_id")

    # Ensure item exists
    item = db.query(ClosetItem).filter(ClosetItem.id == closet_uuid).first()
    if not item:
        raise HTTPException(status_code=404, detail="ClosetItem not found")

    # Save file to disk
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ext = ""
    if file.filename and "." in file.filename:
        ext = "." + file.filename.rsplit(".", 1)[1].lower()

    storage_key = f"{closet_item_id}/{uuid.uuid4()}{ext}"
    abs_path = UPLOAD_DIR / storage_key
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    hasher = hashlib.sha256()
    with abs_path.open("wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            f.write(chunk)

    checksum = hasher.hexdigest()

    # ✅ Define public_url BEFORE using it anywhere
    public_url = f"/files/{storage_key}"

    # ✅ Store on ClosetItem so GET /closet-items can return it
    item.image_path = public_url

    # Create ItemImage record
    img = ItemImage(
        closet_item_id=closet_uuid,
        image_role="original",
        storage_provider="local",
        storage_key=storage_key,
        public_url=public_url,
        mime_type=file.content_type,
        source_type=source_type,
        source_url=source_url,
        source_provider=source_provider,
        status="ready",
        checksum=checksum,
    )
    db.add(img)
    db.flush()  # assigns img.id without committing
    payload={"closet_item_id": str(item.id), "item_image_id": str(img.id)}

    # Mark closet item as processing until cutout exists (your v0.1 behavior)
    item.processing_status = "processing"

    # Create Job stub for background removal (we’ll implement worker later)
    job = Job(
        user_id=item.user_id,
        job_type="background_removal",
        entity_type="closet_item",
        entity_id=item.id,
        status="queued",
        payload={"closet_item_id": str(item.id), "item_image_id": str(img.id)},
    )

    db.add(job)

    db.commit()
    db.refresh(img)

    return img
