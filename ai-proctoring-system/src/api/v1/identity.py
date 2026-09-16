"""
Pre-Exam Identity Verification Endpoints (API v1)
Submits photo ID and live selfie for biometric ArcFace verification with HITL triage.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from src.features.identity_verification.schemas import (
    IdentityVerificationRequest,
    IdentityVerificationResponse
)
from src.features.identity_verification.service import IdentityVerificationService

logger = logging.getLogger("identity_api")

router = APIRouter(prefix="/identity", tags=["Identity Verification"])


@router.post("/verify", response_model=IdentityVerificationResponse)
def verify_identity(payload: IdentityVerificationRequest):
    """
    Submits candidate government photo ID and live webcam selfie.
    Performs ArcFace 512-d feature extraction and cosine similarity comparison.
    Enforces Tri-State Human-in-the-Loop review threshold (>=70% Auto, 40-69.9% HITL, <40% Reject).
    """
    try:
        result = IdentityVerificationService.verify_candidate_identity(payload)
        return result
    except Exception as e:
        logger.error(f"Error during identity verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Identity verification failed: {str(e)}"
        )
