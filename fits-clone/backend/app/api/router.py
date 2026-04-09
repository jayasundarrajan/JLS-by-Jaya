from fastapi import APIRouter
from app.api.routes import users, closet_items, item_images, jobs, closet_item_images, outfits, auth

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

api_router.include_router(
    closet_items.router,
    prefix="/closet-items",
    tags=["closet-items"],
)

api_router.include_router(
    item_images.router,
    prefix="/item-images",
    tags=["item-images"],
)

# ✅ NEW: expose images for a closet item
api_router.include_router(
    closet_item_images.router,
    tags=["closet-items"],
)

api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["jobs"],
)
api_router.include_router(outfits.router, prefix="/outfits", tags=["outfits"])

