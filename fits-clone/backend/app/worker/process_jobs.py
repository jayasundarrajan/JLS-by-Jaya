import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.job import Job
from app.models.item_image import ItemImage
from app.models.closet_item import ClosetItem

UPLOAD_DIR = Path("storage/uploads")


def public_url_to_disk_path(public_url: str) -> Path:
    # "/files/<closet_item_id>/<filename>"
    if not public_url.startswith("/files/"):
        raise ValueError(f"Invalid public_url: {public_url}")
    rel = public_url.replace("/files/", "", 1)
    return UPLOAD_DIR / rel


def process_one_job(db: Session) -> Job | None:
    job = (
        db.query(Job)
        .filter(Job.status == "queued")
        .filter(Job.job_type == "background_removal")
        .order_by(Job.created_at.asc())
        .with_for_update(skip_locked=True)
        .first()
    )

    if not job:
        return None

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)

    try:
        closet_item_id = uuid.UUID(job.payload["closet_item_id"])

        # Get original image
        original = (
            db.query(ItemImage)
            .filter(ItemImage.closet_item_id == closet_item_id)
            .filter(ItemImage.image_role == "original")
            .order_by(ItemImage.created_at.desc())
            .first()
        )

        if not original or not original.public_url:
            raise RuntimeError("Original image not found")

        src_path = public_url_to_disk_path(original.public_url)
        if not src_path.exists():
            raise RuntimeError(f"Original file missing: {src_path}")

        # Create placeholder cutout
        cutout_filename = f"cutout_{uuid.uuid4()}.png"
        cutout_storage_key = f"{closet_item_id}/{cutout_filename}"
        cutout_path = UPLOAD_DIR / cutout_storage_key
        cutout_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(src_path, cutout_path)

        cutout_public_url = f"/files/{cutout_storage_key}"

        cutout = ItemImage(
            closet_item_id=closet_item_id,
            image_role="cutout",
            storage_provider="local",
            storage_key=cutout_storage_key,
            public_url=cutout_public_url,
            mime_type="image/png",
            source_type=original.source_type,
            source_url=original.source_url,
            source_provider=original.source_provider,
            status="ready",
        )
        db.add(cutout)

        # Mark closet item ready
        item = db.query(ClosetItem).filter(ClosetItem.id == closet_item_id).first()
        if item:
            item.processing_status = "ready"

        job.status = "succeeded"
        job.finished_at = datetime.now(timezone.utc)
        job.result = {"cutout_public_url": cutout_public_url}
        job.error_message = None

        db.commit()
        return job

    except Exception as e:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = str(e)
        db.commit()
        return job


def main():
    db = SessionLocal()
    try:
        job = process_one_job(db)
        if not job:
            print("No queued jobs.")
            return
        print(f"Processed job {job.id} → {job.status}")
        if job.error_message:
            print("Error:", job.error_message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
