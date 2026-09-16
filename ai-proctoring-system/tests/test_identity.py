"""
Unit Tests for Identity Verification Feature (Step 1)
"""

import sys
import os
import cv2
import base64
import pytest
import numpy as np

# Add src to sys.path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.features.identity_verification.schemas import (
    IdentityVerificationRequest,
    IdentityVerificationResponse,
    VerificationStatus
)
from src.features.identity_verification.service import IdentityVerificationService
from src.features.identity_verification.nodes import identity_verification_node
from src.core.state import ProctorSessionState


def create_synthetic_face_image(fill_color=(140, 180, 220), shape="oval") -> str:
    """Helper to generate a base64 encoded test face image."""
    img = np.zeros((240, 240, 3), dtype=np.uint8)
    if shape == "oval":
        cv2.ellipse(img, (120, 120), (60, 85), 0, 0, 360, fill_color, -1)
        cv2.circle(img, (100, 100), 10, (40, 40, 40), -1)
        cv2.circle(img, (140, 100), 10, (40, 40, 40), -1)
    elif shape == "rect":
        cv2.rectangle(img, (50, 50), (190, 190), fill_color, -1)
    _, buf = cv2.imencode(".jpg", img)
    return f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"


def test_identity_verification_verified_above_threshold():
    """Verifies that identical or highly similar faces pass with VERIFIED status (>= 70%)."""
    doc_b64 = create_synthetic_face_image((150, 190, 230), shape="oval")
    selfie_b64 = create_synthetic_face_image((150, 190, 230), shape="oval")

    req = IdentityVerificationRequest(
        candidate_id="CAND-001",
        document_image_b64=doc_b64,
        selfie_image_b64=selfie_b64,
        document_type="aadhaar"
    )

    res = IdentityVerificationService.verify_candidate_identity(req)
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified is True
    assert res.needs_human_review is False
    assert res.match_confidence >= 0.70
    assert "70.0%" in res.review_reason or "%" in res.match_percentage


def test_identity_verification_rejected_below_threshold():
    """Verifies that completely dissimilar inputs return REJECTED status (< 40%)."""
    # Force low similarity by comparing an oval with an inverted contrast rectangle
    doc_b64 = create_synthetic_face_image((255, 255, 255), shape="oval")
    # Black blank
    blank = np.zeros((240, 240, 3), dtype=np.uint8)
    # Add tiny corner dot only
    blank[0:10, 0:10] = (10, 10, 10)
    _, buf = cv2.imencode(".jpg", blank)
    blank_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"

    req = IdentityVerificationRequest(
        candidate_id="CAND-002",
        document_image_b64=doc_b64,
        selfie_image_b64=blank_b64,
        document_type="pan"
    )

    res = IdentityVerificationService.verify_candidate_identity(req)
    assert res.status == VerificationStatus.REJECTED
    assert res.verified is False
    assert res.needs_human_review is False
    assert res.match_confidence < 0.40


def test_identity_verification_pending_human_review_corridor():
    """Verifies that borderline scores (40% - 69.9%) trigger PENDING_HUMAN_REVIEW fallback."""
    # Test service decision logic explicitly for the review corridor
    emb1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    # Create vector with 0.55 cosine similarity
    angle = np.arccos(0.55)
    emb2 = np.array([np.cos(angle), np.sin(angle), 0.0], dtype=np.float32)

    sim = IdentityVerificationService.compute_similarity(emb1, emb2)
    assert 0.40 <= sim < 0.70

    # Test with mock request and custom mock embeddings
    req = IdentityVerificationRequest(
        candidate_id="CAND-003",
        document_image_b64=create_synthetic_face_image(),
        selfie_image_b64=create_synthetic_face_image(),
        document_type="driving_license"
    )
    
    # Temporarily mock compute_similarity to evaluate corridor threshold behavior
    orig_sim = IdentityVerificationService.compute_similarity
    try:
        IdentityVerificationService.compute_similarity = classmethod(lambda cls, e1, e2: 0.58)
        res = IdentityVerificationService.verify_candidate_identity(req)
        assert res.status == VerificationStatus.PENDING_HUMAN_REVIEW
        assert res.verified is False
        assert res.needs_human_review is True
        assert "Escalated for human proctor sign-off" in res.review_reason
    finally:
        IdentityVerificationService.compute_similarity = orig_sim


def test_identity_verification_invalid_payload():
    """Verifies that invalid base64 payloads return REJECTED cleanly without raising unhandled exceptions."""
    req = IdentityVerificationRequest(
        candidate_id="CAND-ERR",
        document_image_b64="not_base64_data",
        selfie_image_b64="also_corrupted",
        document_type="passport"
    )
    res = IdentityVerificationService.verify_candidate_identity(req)
    assert res.status == VerificationStatus.REJECTED
    assert res.verified is False
    assert res.match_confidence == 0.0
    assert "could not be decoded" in res.review_reason.lower()


def test_identity_verification_node_state_update():
    """Verifies that the LangGraph identity verification node updates session state correctly."""
    frame = np.full((100, 100, 3), 200, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame)
    frame_bytes = buf.tobytes()

    # Case 1: Normal single face
    state_normal: ProctorSessionState = {
        "session_id": "sess_101",
        "candidate_id": "cand_101",
        "timestamp": "2026-09-15T12:00:00Z",
        "primary_frame_bytes": frame_bytes,
        "secondary_frame_bytes": None,
        "audio_chunk_bytes": None,
        "audio_transcript": None,
        "face_count": 1,
        "face_matched": False,
        "detected_objects": [],
        "visual_anomalies": [],
        "audio_anomalies": [],
        "policy_violations": [],
        "risk_score_delta": 0.0,
        "cumulative_risk_score": 0.0,
        "warning_count": 0,
        "evidence_events": [],
        "orchestrator_decision": "CONTINUE"
    }

    result = identity_verification_node(state_normal)
    assert result["face_matched"] is True

    # Case 2: Multiple faces (anomaly logged)
    state_multi = dict(state_normal)
    state_multi["face_count"] = 2
    result_multi = identity_verification_node(state_multi)
    assert result_multi["face_matched"] is False
    assert len(result_multi["visual_anomalies"]) == 1
    assert result_multi["visual_anomalies"][0]["type"] == "MULTIPLE_FACES_DETECTED"
    assert len(result_multi["evidence_events"]) == 1
    assert result_multi["evidence_events"][0]["severity"] == "HIGH"
