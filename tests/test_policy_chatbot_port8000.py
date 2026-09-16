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
    from app.ai.policy_chatbot import policy_chatbot
    policy_chatbot.set_active_company("techhire_global")

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


def test_policy_document_ingestion_and_breach_definition():
    doc_text = """
    ACME GLOBAL CLOUD TESTING BYLAWS 2026
    Section 3.1: Candidate Solitary Room Isolation
    The examinee must be alone in a secluded room. Double person or companion intrusion is prohibited.

    Section 4.5: Prohibited Cellular Smartphones
    Cellular phones, smartphones, and communication accessories are barred from the testing desk.

    Section 4.8: Auxiliary Displays and Laptops
    Secondary laptops, external monitors, and tablet displays are strictly banned.
    """

    res = client.post("/api/v1/policies/ingest-document", json={
        "company_name": "Acme Global Cloud",
        "industry": "Software Engineering",
        "strictness": "MAXIMUM_STRICT",
        "document_text": doc_text
    })

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["company_id"] == "acme_global_cloud"
    assert "defined_breaches" in data
    breaches = data["defined_breaches"]
    assert "PHONE" in breaches
    assert "LAPTOP" in breaches
    assert "PERSON" in breaches

    assert "Section 4.5" in breaches["PHONE"]["clause"]
    assert "Section 4.8" in breaches["LAPTOP"]["clause"]
    assert "Section 3.1" in breaches["PERSON"]["clause"]

    # Verify active company is now Acme Global Cloud
    comp_res = client.get("/api/v1/policies/companies")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["active_company_id"] == "acme_global_cloud"


def test_policy_allows_mobile_phones_no_violation_no_evidence_no_warning(monkeypatch):
    import numpy as np
    import cv2
    import base64
    from app.api import endpoints

    # 1. Ingest policy document that allows mobile phones
    policy_doc = """
    CLIENT INTEGRITY DIRECTIVE - MOBILE ENABLED
    Section 1.1: Permitted Cellular Devices & 2FA
    Mobile phones and cellular devices are explicitly allowed for candidate dual-factor authentication.
    Section 4.3: Secondary Laptops
    Secondary laptops and external displays are strictly banned.
    Section 5.1: Solitary Presence
    Solitary room isolation is mandatory; second persons are prohibited.
    """

    ingest_res = client.post("/api/v1/policies/ingest-document", json={
        "company_name": "Mobile Friendly Tech",
        "industry": "Software Engineering",
        "strictness": "MEDIUM",
        "document_text": policy_doc,
        "phone_allowed": True,
        "laptop_allowed": False,
        "person_allowed": False
    })
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["defined_breaches"]["PHONE"]["allowed"] is True
    assert ingest_data["defined_breaches"]["LAPTOP"]["allowed"] is False
    assert ingest_data["defined_breaches"]["PERSON"]["allowed"] is False

    # 2. Mock detector detecting a cell phone and a single person
    def mock_detect_phone(img):
        return {
            "detections": [
                {"object": "cell phone", "confidence": 0.96, "box": [20, 20, 50, 80]},
                {"object": "person", "confidence": 0.92, "box": [40, 40, 220, 220]}
            ]
        }

    monkeypatch.setattr(endpoints.detector, "detect", mock_detect_phone)

    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode('.jpg', dummy_frame)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')

    # 3. Post frame scan
    scan_res = client.post("/api/v1/sessions/scan-frame", json={
        "frame_data": b64,
        "student_id": "STU-PHONE-PERMITTED"
    })
    assert scan_res.status_code == 200
    scan_data = scan_res.json()

    # The detector sees the phone, but because the RAG policy allows it:
    # - status must be CLEAN
    # - violations must be empty []
    # - no evidence_url generated
    # - no warning_chat_message generated
    assert scan_data["phone_detected"] is True
    assert scan_data["status"] == "CLEAN"
    assert scan_data["violations"] == []
    assert scan_data["evidence_url"] is None
    assert scan_data["warning_chat_message"] is None

    # 4. Check admin breach dossier: must NOT contain any breach for STU-PHONE-PERMITTED
    admin_res = client.get("/api/v1/admin/policy-breaches?student_id=STU-PHONE-PERMITTED")
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert admin_data["total_breaches"] == 0
    assert len(admin_data["breaches"]) == 0


def test_policy_auto_detects_allowed_mobile_from_linguistic_text():
    # Ingest policy containing "except the mobile" without explicit boolean flag
    policy_doc = """
    POLICY ON WORKSTATION HARDWARE:
    Except the mobile phones which are allowed for login verification, all other electronic communication devices are prohibited.
    Auxiliary laptops and multiple persons in the room are strictly forbidden.
    """

    ingest_res = client.post("/api/v1/policies/ingest-document", json={
        "company_name": "Linguistic Regex Enterprise",
        "industry": "Consulting",
        "strictness": "HIGH",
        "document_text": policy_doc
    })
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["defined_breaches"]["PHONE"]["allowed"] is True
    assert ingest_data["defined_breaches"]["LAPTOP"]["allowed"] is False
    assert ingest_data["defined_breaches"]["PERSON"]["allowed"] is False


def test_policy_auto_detects_multi_item_exemption_except_mobile_laptop_all():
    # User exact prompt: "except the mobile laptop all"
    ingest_res = client.post("/api/v1/policies/ingest-document", json={
        "company_name": "Multi Item Exemption Corp",
        "industry": "Software & Cloud Engineering",
        "strictness": "STANDARD",
        "document_text": "except the mobile laptop all"
    })
    assert ingest_res.status_code == 200
    data = ingest_res.json()
    assert data["defined_breaches"]["PHONE"]["allowed"] is True
    assert data["defined_breaches"]["LAPTOP"]["allowed"] is True
    assert data["defined_breaches"]["PERSON"]["allowed"] is False
    assert "PHONE, LAPTOP" in data["document_summary"]
    # Verify rule description does NOT cite exemption text as violation
    assert "except the mobile laptop all" not in data["defined_breaches"]["LAPTOP"]["rule"]

