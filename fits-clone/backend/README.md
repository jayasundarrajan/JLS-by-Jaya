FITS Backend — v0.1

Overview

FITS is a backend service for managing a user’s digital wardrobe (“closet items”) and associated images.
Version v0.1 focuses on establishing a reliable end-to-end pipeline for:
       - Creating closet items
       - Uploading item images
       - Persisting image references
       - Retrieving items with browser-ready image URLs
No frontend or authentication is implemented yet. All testing is done via Swagger or direct HTTP requests.


Tech Stack

    - FastAPI (API framework)
    - PostgreSQL (database running via Docker)
    - SQLAlchemy + Alembic (ORM + migrations)
    - Uvicorn (ASGI server)
    - Local file storage for images
    - TablePlus (DB viewer for inspecting tables/rows during development)


How to Run

    1. STart Postgres with Docker
            docker compose up -d
    2. Run alembic migrations
            alembic upgrade head
    3. Start API server 
            uvicorn app.main:app --reload --port 8000
            swagger: http://127.0.0.1:8000/docs
            

What v0.1 Guarantees

✅ Closet items can be created
✅ Images can be uploaded
✅ Images are persisted to disk
✅ Closet items return image_path + browser-ready image_url
✅ DB changes managed via Alembic migrations
✅ Postgres runs via Docker, inspectable via TablePlus


Out of Scope (Future Versions):

Authentication (real user sessions)
Background removal worker + cutout generation
Frontend UI
Editing/deleting items
Multiple image roles fully surfaced in closet item responses