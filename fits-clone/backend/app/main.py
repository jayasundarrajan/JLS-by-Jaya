from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router


app = FastAPI(title="FITS Clone API")

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve uploaded files (dev only)
app.mount("/files", StaticFiles(directory="storage/uploads"), name="files")

app.include_router(api_router)
