import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_and_onboarding_flow():
    # 1. Invalid Password -> 401 Unauthorized
    bad_login = client.post("/api/v1/auth/login", json={"username": "STU-001", "password": "wrongcode"})
    assert bad_login.status_code == 401

    # 2. Valid Password ('proctor2026') -> 200 OK & Email Notification Sent
    good_login = client.post("/api/v1/auth/login", json={"username": "STU-001", "password": "proctor2026"})
    assert good_login.status_code == 200
    auth_data = good_login.json()
    token = auth_data["access_token"]
    assert token.startswith("tok-STU-001")
    assert auth_data["email_sent"] is True
    assert "email_sent_to" in auth_data

    # 3. Privacy Consent without checking box -> 400 Bad Request
    bad_consent = client.post("/api/v1/onboarding/consent", json={"session_token": token, "consent_agreed": False})
    assert bad_consent.status_code == 400

    # 4. Privacy Consent checked -> 200 OK
    good_consent = client.post("/api/v1/onboarding/consent", json={"session_token": token, "consent_agreed": True})
    assert good_consent.status_code == 200
    assert good_consent.json()["status"] == "CONSENT_RECORDED"

    # 5. Readiness Validation -> 200 OK
    readiness = client.post(
        "/api/v1/onboarding/readiness-check",
        json={
            "session_token": token,
            "media_api_supported": True,
            "file_api_supported": True,
            "screen_resolution_valid": True,
            "identity_photo_provided": True
        }
    )
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "READY_FOR_SESSION"

    # 6. Check Onboarding Status
    status_res = client.get("/api/v1/onboarding/status", headers={"X-Session-Token": token})
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "READY_FOR_SESSION"
