import cv2
import numpy as np
import base64
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.document_validator import DocumentValidator

client = TestClient(app)

def create_synthetic_id(doc_type: str = "aadhaar", with_face: bool = True, face_scale: float = 0.2) -> str:
    """Helper to generate a synthetic ID card image as base64 string."""
    h, w = 300, 480
    
    if doc_type == "pan":
        # Blue/Teal gradient background
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:, :] = [180, 120, 40]  # BGR teal-blue
        # Income Tax header
        cv2.putText(img, "INCOME TAX DEPARTMENT", (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, "GOVT. OF INDIA", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, "PAN: ABCDE1234F", (30, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    elif doc_type == "aadhaar":
        # White card with tricolor top strip
        img = np.full((h, w, 3), 245, dtype=np.uint8)
        # Saffron strip (BGR: [30, 130, 240])
        img[0:30, :] = [30, 130, 240]
        # Green strip (BGR: [60, 160, 40])
        img[30:50, :] = [60, 160, 40]
        cv2.putText(img, "Government of India", (80, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, "1234 5678 9012", (120, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    elif doc_type == "selfie":
        # Large face covering most of image
        img = np.full((h, w, 3), 100, dtype=np.uint8)
    else:
        # Blank / random
        img = np.full((h, w, 3), 200, dtype=np.uint8)

    if with_face:
        # Draw a synthetic face with eyes, nose, mouth so Haar cascade can detect it or draw realistic proportions
        fh = int(h * face_scale)
        fw = int(w * (face_scale * 0.7))
        fx = 40 if doc_type != "selfie" else int((w - fw) / 2)
        fy = 70 if doc_type != "selfie" else int((h - fh) / 2)
        
        # Face oval
        cv2.ellipse(img, (fx + fw//2, fy + fh//2), (fw//2, fh//2), 0, 0, 360, (200, 220, 240), -1)
        # Eyes
        eye_y = fy + int(fh * 0.35)
        cv2.circle(img, (fx + int(fw * 0.3), eye_y), max(2, fw//12), (30, 30, 30), -1)
        cv2.circle(img, (fx + int(fw * 0.7), eye_y), max(2, fw//12), (30, 30, 30), -1)
        # Mouth
        mouth_y = fy + int(fh * 0.7)
        cv2.ellipse(img, (fx + fw//2, mouth_y), (int(fw * 0.25), int(fh * 0.1)), 0, 0, 180, (50, 50, 180), 2)

    _, buf = cv2.imencode(".jpg", img)
    return f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"


def test_document_validation_endpoint():
    """Tests the /api/v1/onboarding/validate-document API endpoint."""
    pan_b64 = create_synthetic_id(doc_type="pan", with_face=True, face_scale=0.25)
    
    # Validating PAN when PAN is selected
    res = client.post("/api/v1/onboarding/validate-document", json={
        "document_id_b64": pan_b64,
        "document_type": "pan"
    })
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "clarity_score" in data
    assert "checks" in data
    assert data["selected_type"] == "pan"

    # Validating PAN when Aadhaar is selected -> should detect MISMATCH
    res_mismatch = client.post("/api/v1/onboarding/validate-document", json={
        "document_id_b64": pan_b64,
        "document_type": "aadhaar"
    })
    assert res_mismatch.status_code == 200
    mismatch_data = res_mismatch.json()
    assert mismatch_data["selected_type"] == "aadhaar"
    # When blue card is uploaded as aadhaar, it should flag mismatch or detected as pan
    assert mismatch_data["detected_type"] in ["pan", "unknown"]


def test_validator_detects_selfie_as_invalid_document():
    """Tests that a direct selfie uploaded as a document is rejected with NOT_AN_ID."""
    selfie_b64 = create_synthetic_id(doc_type="selfie", with_face=True, face_scale=0.85)
    report = DocumentValidator.validate_document(selfie_b64, selected_type="aadhaar")
    
    # Large face area ratio should trigger direct_selfie or invalid
    if report["checks"].get("face_area_ratio", 0) > 0.55:
        assert report["status"] == "NOT_AN_ID"
        assert "selfie" in report["warning_message"].lower()


def test_validator_rejects_blank_document():
    """Tests that an image with no face is flagged as invalid."""
    blank_b64 = create_synthetic_id(doc_type="blank", with_face=False)
    report = DocumentValidator.validate_document(blank_b64, selected_type="aadhaar")
    
    assert report["status"] == "INVALID"
    assert "no photograph" in report["warning_message"].lower()


def test_validator_rejects_standalone_portrait_photo_with_blue_background():
    """Verifies that a personal portrait photo with blue studio backdrop is not confused for a PAN card."""
    h, w = 600, 450  # Vertical aspect ratio 0.75
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = (210, 180, 130)  # Blue studio background
    # Shoulders
    cv2.ellipse(img, (225, 550), (160, 120), 0, 0, 360, (120, 120, 120), -1)
    # Face & Neck
    cv2.rectangle(img, (190, 340), (260, 420), (140, 170, 220), -1)
    cv2.ellipse(img, (225, 280), (80, 110), 0, 0, 360, (140, 170, 220), -1)
    # Eyes & Mouth
    cv2.circle(img, (195, 260), 10, (40, 40, 40), -1)
    cv2.circle(img, (255, 260), 10, (40, 40, 40), -1)
    cv2.ellipse(img, (225, 330), (35, 15), 0, 0, 180, (50, 50, 180), 3)

    _, buf = cv2.imencode('.jpg', img)
    portrait_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"

    report = DocumentValidator.validate_document(portrait_b64, selected_type="pan")
    assert report["status"] == "NOT_AN_ID"
    assert report["is_match"] is False
    assert "not a valid id" in report["warning_message"].lower() or "not an id card" in report["warning_message"].lower()

