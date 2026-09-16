import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.session import engine, Base
from app.api.endpoints import router as api_router

# Initialize database tables
Base.metadata.create_all(bind=engine)
try:
    with engine.connect() as conn:
        res = conn.exec_driver_sql("PRAGMA table_info(candidate_submissions)").fetchall()
        cols = [r[1] for r in res]
        if "device_duration_seconds" not in cols:
            conn.exec_driver_sql("ALTER TABLE candidate_submissions ADD COLUMN device_duration_seconds FLOAT DEFAULT 0.0")
            conn.commit()
except Exception:
    pass

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

from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheStaticMiddleware)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
