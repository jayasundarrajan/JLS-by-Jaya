import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.job import Job
from app.models.closet_item import ClosetItem
from app.models.item_image import ItemImage

from rembg import remove

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")


def public_url_to_disk_path(public_url: str) -> Path:
    # public_url: "/files/<closet_item_id>/<filename>"
    if not public_url or not public_url.startswith("/files/"):
        raise ValueError(f"Invalid public_url: {public_url}")
    rel = public_url.replace("/files/", "", 1)
    return UPLOAD_DIR / rel


@router.post("/process-next")
def process_next_job(db: Session = Depends(get_db)):
    job = (
        db.query(Job)
        .filter(Job.status == "queued", Job.job_type == "background_removal")
        .order_by(Job.created_at.desc())
        .first()
    )

    if not job:
        return {"status": "no_jobs"}

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.flush()

    item = db.query(ClosetItem).filter(ClosetItem.id == job.entity_id).first()
    if not item:
        job.status = "failed"
        job.error_message = "ClosetItem not found"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=404, detail="ClosetItem not found for job")

    # ✅ Prefer the specific original image referenced by THIS job
    original = None
    payload_item_image_id = None

    if job.payload and isinstance(job.payload, dict):
        payload_item_image_id = job.payload.get("item_image_id")

    if payload_item_image_id:
        try:
            img_uuid = uuid.UUID(str(payload_item_image_id))
            original = (
                db.query(ItemImage)
                .filter(
                    ItemImage.id == img_uuid,
                    ItemImage.closet_item_id == item.id,
                    ItemImage.image_role == "original",
                )
                .first()
            )
        except ValueError:
            original = None  # fall back below

    # Backward-compatible fallback for old jobs that had no item_image_id in payload
    if not original:
        original = (
            db.query(ItemImage)
            .filter(
                ItemImage.closet_item_id == item.id,
                ItemImage.image_role == "original",
            )
            .order_by(ItemImage.created_at.desc())
            .first()
        )

    if not original or not original.public_url:
        job.status = "failed"
        job.error_message = "Original image not found (or missing public_url)"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=404, detail="Original image not found")

    # --- REAL CUTOUT GENERATION ---
    try:
        src_path = public_url_to_disk_path(original.public_url)
        if not src_path.exists():
            raise FileNotFoundError(f"Original file missing on disk: {src_path}")

        input_bytes = src_path.read_bytes()
        output_bytes = remove(input_bytes)

        cutout_filename = f"cutout_{uuid.uuid4()}.png"
        cutout_storage_key = f"{item.id}/{cutout_filename}"
        cutout_path = UPLOAD_DIR / cutout_storage_key
        cutout_path.parent.mkdir(parents=True, exist_ok=True)
        cutout_path.write_bytes(output_bytes)

        cutout_public_url = f"/files/{cutout_storage_key}"

        cutout = ItemImage(
            closet_item_id=item.id,
            image_role="cutout",
            storage_provider="local",
            storage_key=cutout_storage_key,
            public_url=cutout_public_url,
            mime_type="image/png",
            source_type=original.source_type,
            source_url=original.source_url,
            source_provider=original.source_provider,
            status="ready",
            checksum=None,
        )
        db.add(cutout)
        db.flush()  # assigns cutout.id

        item.processing_status = "ready"

        job.status = "succeeded"
        job.result = {
            "cutout_item_image_id": str(cutout.id),
            "cutout_public_url": cutout_public_url,
            "original_item_image_id": str(original.id),
        }
        job.error_message = None
        job.finished_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "status": "processed",
            "job_id": str(job.id),
            "closet_item_id": str(item.id),
            "original_item_image_id": str(original.id),
            "cutout_item_image_id": str(cutout.id),
            "cutout_public_url": cutout_public_url,
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Job failed: {e}")
