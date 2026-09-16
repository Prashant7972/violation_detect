"""
API v1 Router Aggregator
Combines Candidate Sessions, Identity Verification, and Proctor Review routes.
"""

from fastapi import APIRouter

from src.api.v1.sessions import router as sessions_router
from src.api.v1.identity import router as identity_router
from src.api.v1.proctor_review import router as proctor_router
from src.api.v1.chat import router as chat_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(identity_router)
api_v1_router.include_router(proctor_router)
api_v1_router.include_router(chat_router)
