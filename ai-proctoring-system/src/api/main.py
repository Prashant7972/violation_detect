"""
AI Remote Proctoring System - Main API Gateway
FastAPI Application Entrypoint
Provides multi-tenant routing, WebSocket streaming, and HITL human proctor dashboard integration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.api.v1.router import api_v1_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("proctor_main_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and graceful shutdown."""
    logger.info("Initializing AI Remote Proctoring System API Gateway...")
    logger.info(f"Environment: {settings.APP_ENV} | Model: {settings.GEMINI_MODEL_ID}")
    yield
    logger.info("Shutting down AI Remote Proctoring System API Gateway gracefully.")


app = FastAPI(
    title="AI Remote Proctoring System API",
    description=(
        "Next-Generation Multi-modal AI Remote Proctoring System powered by LangGraph, "
        "Google Gemini 2.5 Flash, ArcFace Biometrics, and Human-in-the-Loop Governance."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for proctor dashboard and candidate client frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount versioned API routes
app.include_router(api_v1_router)


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import Request

# Mount Static Files for Proctoring Dashboard Web UI
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# Mount Static Evidence Directory for Violation Proof Keyframes
EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evidence"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")


@app.get("/dashboard", tags=["Dashboard"])
def dashboard():
    """Redirects to the interactive Proctoring Web Dashboard."""
    return RedirectResponse(url="/static/index.html")


@app.get("/", tags=["System"])
def root(request: Request):
    """Service identity endpoint or web dashboard based on client Accept header."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not "*/*" in accept:
        return RedirectResponse(url="/static/index.html")
    return {
        "service": "AI Remote Proctoring System API",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "dashboard_url": "/dashboard",
        "api_v1_prefix": "/api/v1"
    }


@app.get("/health", tags=["System"])
def health_check():
    """Liveness and readiness health probe."""
    return {
        "status": "HEALTHY",
        "engine": "LangGraph + Gemini 2.5 Flash",
        "environment": settings.APP_ENV
    }
