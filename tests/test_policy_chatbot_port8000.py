import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_message_endpoint_prohibited_phone():
    res = client.post("/api/v1/chat/message", json={
        "query": "Is a mobile phone allowed during the exam?",
        "student_id": "STU-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 0
    assert any("4.2" in c or "Academic Integrity" in c for c in data.get("citations", []))
    assert "suggested_questions" in data


def test_chat_message_endpoint_double_person():
    res = client.post("/api/v1/chat/message", json={
        "query": "Can another person or friend sit with me in the room?",
        "student_id": "STU-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "isolation" in data["response"].lower() or "room" in data["response"].lower()


def test_chat_suggested_questions():
    res = client.get("/api/v1/chat/suggested")
    assert res.status_code == 200
    data = res.json()
    assert "suggested_questions" in data
    assert len(data["suggested_questions"]) >= 3


def test_chat_violation_warning_mobile_phone_no_termination():
    res = client.post("/api/v1/chat/violation-warning", json={
        "violation_type": "MOBILE_PHONE_DETECTED",
        "student_id": "STU-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Mobile Phone" in data["warning_title"]
    assert "NOT been terminated" in data["warning_message"]
    assert data["can_terminate"] is False
    assert data["is_warning"] is True


def test_chat_violation_warning_secondary_laptop_no_termination():
    res = client.post("/api/v1/chat/violation-warning", json={
        "violation_type": "SECONDARY_LAPTOP_DETECTED",
        "student_id": "STU-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Laptop" in data["warning_title"] or "Screen" in data["warning_title"]
    assert "NOT been terminated" in data["warning_message"]
    assert data["can_terminate"] is False


def test_chat_violation_warning_double_person_no_termination():
    res = client.post("/api/v1/chat/violation-warning", json={
        "violation_type": "MULTIPLE_PERSONS_IN_FRAME",
        "student_id": "STU-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Person" in data["warning_title"] or "Occupants" in data["warning_title"]
    assert "NOT been terminated" in data["warning_message"]
    assert data["can_terminate"] is False


def test_scan_live_frame_populates_warning_chat_message(monkeypatch):
    import numpy as np
    import cv2
    import base64
    from app.api import endpoints

    # Mock detector to simulate a mobile phone detection
    def mock_detect(img):
        return {
            "detections": [
                {"object": "cell phone", "confidence": 0.95, "box": [10, 10, 50, 50]},
                {"object": "person", "confidence": 0.90, "box": [50, 50, 200, 200]}
            ]
        }

    monkeypatch.setattr(endpoints.detector, "detect", mock_detect)

    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode('.jpg', dummy_frame)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')

    res = client.post("/api/v1/sessions/scan-frame", json={
        "frame_data": b64,
        "student_id": "STU-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VIOLATION"
    assert data["phone_detected"] is True
    assert data["warning_chat_message"] is not None
    assert "mobile phone" in data["warning_chat_message"].lower()
    assert "not been terminated" in data["warning_chat_message"].lower()


def test_client_company_policies_listing_and_switch():
    # 1. List companies
    res = client.get("/api/v1/policies/companies")
    assert res.status_code == 200
    data = res.json()
    assert "active_company_id" in data
    assert len(data["companies"]) >= 3
    comp_ids = [c["id"] for c in data["companies"]]
    assert "techhire_global" in comp_ids
    assert "nta_standard" in comp_ids

    # 2. Switch company
    sw_res = client.post("/api/v1/policies/companies/active", json={"company_id": "nta_standard"})
    assert sw_res.status_code == 200
    sw_data = sw_res.json()
    assert sw_data["success"] is True
    assert sw_data["active_company"]["id"] == "nta_standard"


def test_admin_policy_breaches_collection(monkeypatch):
    import numpy as np
    import cv2
    import base64
    from app.api import endpoints

    def mock_detect_laptop(img):
        return {
            "detections": [
                {"object": "laptop", "confidence": 0.92, "box": [15, 15, 60, 60]},
                {"object": "person", "confidence": 0.88, "box": [50, 50, 200, 200]}
            ]
        }

    monkeypatch.setattr(endpoints.detector, "detect", mock_detect_laptop)

    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode('.jpg', dummy_frame)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')

    # Post frame with laptop violation
    res = client.post("/api/v1/sessions/scan-frame", json={
        "frame_data": b64,
        "student_id": "STU-ADMIN-TEST"
    })
    assert res.status_code == 200

    # Fetch admin breach dossier
    admin_res = client.get("/api/v1/admin/policy-breaches?student_id=STU-ADMIN-TEST")
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert admin_data["total_breaches"] >= 1
    first_breach = admin_data["breaches"][0]
    assert first_breach["student_id"] == "STU-ADMIN-TEST"
    assert "laptop" in first_breach["evidence_url"].lower() or "violation" in first_breach["evidence_url"].lower()
    assert "clause" in first_breach["policy_clause"].lower() or "sec" in first_breach["policy_clause"].lower()


