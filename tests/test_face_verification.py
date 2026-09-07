import cv2
import base64
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_synthetic_face_b64(fill_color=(120, 150, 200)) -> str:
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    # Draw head / face structure
    cv2.ellipse(img, (100, 100), (50, 70), 0, 0, 360, fill_color, -1)
    cv2.circle(img, (80, 80), 8, (255, 255, 255), -1)
    cv2.circle(img, (120, 80), 8, (255, 255, 255), -1)
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def test_pre_auth_face_verification_and_login():
    doc_b64 = create_synthetic_face_b64((120, 150, 200))
    selfie_b64 = create_synthetic_face_b64((120, 150, 200))

    # 1. Submit Pre-Auth Identity Verification
    verify_res = client.post(
        "/api/v1/onboarding/verify-id",
        json={
            "username": "STU-001",
            "email": "candidate@example.com",
            "document_id_b64": doc_b64,
            "live_selfie_b64": selfie_b64
        }
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["status"] == "VERIFIED"
    assert data["match_confidence"] >= 0.70
    assert "candidate@example.com" in data["email_sent_to"]

    # Retrieve password sent to email (simulating candidate opening email)
    from app.api.endpoints import REGISTERED_CREDENTIALS
    generated_password = REGISTERED_CREDENTIALS["STU-001"]

    # 2. Authenticate with Username & Received Password
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username": "STU-001",
            "password": generated_password
        }
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["username"] == "STU-001"
    assert login_data["access_token"].startswith("tok-STU-001")
    assert login_data["email_sent"] is True
    assert login_data["email_sent_to"] == "candidate@example.com"


def test_multi_position_photo_extraction():
    """Verify face verification succeeds regardless of whether photo is on Left, Middle, or Right of ID card."""
    from app.ai.face_verifier import FaceVerifier
    
    selfie = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.ellipse(selfie, (100, 100), (50, 70), 0, 0, 360, (120, 150, 200), -1)

    for position in ["left", "middle", "right"]:
        card = np.zeros((200, 600, 3), dtype=np.uint8)
        # Position face portrait in different areas
        if position == "left":
            cx = 100
        elif position == "middle":
            cx = 300
        else:
            cx = 500

        cv2.ellipse(card, (cx, 100), (50, 70), 0, 0, 360, (120, 150, 200), -1)
        res = FaceVerifier.compare_faces(card, selfie)
        assert res["verified"] is True, f"Failed for photo at {position} position: {res}"
        assert res["match_confidence"] >= 0.70


def test_non_matching_face_rejection():
    """Verify that different persons or non-matching facial features evaluate < 70% and are REJECTED."""
    from app.ai.face_verifier import FaceVerifier
    
    # Face A (e.g. Person 1)
    face_a = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.ellipse(face_a, (100, 100), (50, 70), 0, 0, 360, (220, 50, 50), -1) # Red hue, wide head

    # Face B (e.g. Completely Different Person 2)
    face_b = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(face_b, (30, 30), (170, 170), (40, 200, 40), -1) # Green hue, square contour

    res = FaceVerifier.compare_faces(face_a, face_b)
    assert res["verified"] is False, f"Expected non-matching faces to be rejected, got: {res}"
    assert res["match_confidence"] < 0.70


def test_document_type_selection_and_verification():
    """Verify document type options (Aadhaar, PAN, Driving License, Passport) work end-to-end."""
    from app.ai.face_verifier import FaceVerifier

    doc_b64 = create_synthetic_face_b64((120, 150, 200))
    selfie_b64 = create_synthetic_face_b64((120, 150, 200))

    for doc_type in ["aadhaar", "pan", "driving_license", "passport"]:
        # Test API endpoint with document_type
        verify_res = client.post(
            "/api/v1/onboarding/verify-id",
            json={
                "username": f"STU-{doc_type.upper()[:3]}",
                "email": f"{doc_type}@example.com",
                "document_id_b64": doc_b64,
                "live_selfie_b64": selfie_b64,
                "document_type": doc_type
            }
        )
        assert verify_res.status_code == 200, f"Failed for {doc_type}: {verify_res.text}"
        data = verify_res.json()
        assert data["status"] == "VERIFIED"
        assert data["match_confidence"] >= 0.70
        assert data.get("password_issued") is None
        assert f"{doc_type}@example.com" in data["email_sent_to"]
        from app.api.endpoints import REGISTERED_CREDENTIALS
        assert f"STU-{doc_type.upper()[:3]}" in REGISTERED_CREDENTIALS


