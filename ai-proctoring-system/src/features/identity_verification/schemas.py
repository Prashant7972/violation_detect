"""
Schemas & Data Contracts for Identity Verification Feature
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    REJECTED = "REJECTED"


class IdentityVerificationRequest(BaseModel):
    """Payload for submitting photo ID and live webcam selfie."""
    candidate_id: str = Field(..., description="Unique student or candidate identifier")
    document_image_b64: str = Field(..., description="Base64 encoded photo ID image")
    selfie_image_b64: str = Field(..., description="Base64 encoded live webcam selfie image")
    document_type: str = Field(default="aadhaar", description="Type of ID document (aadhaar, pan, driving_license, passport)")


class IdentityVerificationResponse(BaseModel):
    """Output contract containing biometric match results and human review triage flags."""
    candidate_id: str
    status: VerificationStatus
    verified: bool = Field(..., description="True if confidence >= threshold")
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    match_percentage: str = Field(..., description="Formatted similarity percentage (e.g. 84.5%)")
    document_type: str
    needs_human_review: bool = Field(default=False, description="True if match is borderline and requires proctor confirmation")
    review_reason: Optional[str] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)


class HumanReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class HumanReviewActionRequest(BaseModel):
    """Payload for a human proctor overriding or signing off on a pending review."""
    candidate_id: str
    reviewer_id: str
    decision: HumanReviewDecision
    notes: Optional[str] = None
