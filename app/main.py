import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.session import engine, Base
from app.api.endpoints import router as api_router

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Ensure folders exist
os.makedirs(settings.EVIDENCE_DIR, exist_ok=True)
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Mount Static Files for Web Client UI and Evidence Screenshots
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
app.mount("/evidence", StaticFiles(directory=settings.EVIDENCE_DIR), name="evidence")

@app.get("/")
def root():
    return {
        "title": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "web_ui": "/static/index.html",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
