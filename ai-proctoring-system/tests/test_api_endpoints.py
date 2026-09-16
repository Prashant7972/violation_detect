"""
Comprehensive FastAPI Gateway Integration Tests
Validates all REST endpoints and WebSocket channels for candidate sessions,
identity verification, and the proctor review portal.
"""

import base64
import numpy as np
import cv2
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.v1.sessions import ACTIVE_SESSIONS


def create_dummy_base64_image(color=(100, 150, 200), width=100, height=100) -> str:
    """Generates an in-memory encoded image for testing."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return base64.b64encode(buf).decode("utf-8")


@pytest.fixture
def client():
    ACTIVE_SESSIONS.clear()
    with TestClient(app) as test_client:
        yield test_client


class TestSystemHealthEndpoints:
    """Validates baseline service liveness and meta information."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPERATIONAL"
        assert data["service"] == "AI Remote Proctoring System API"
        assert data["version"] == "1.0.0"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"
        assert "LangGraph" in data["engine"]


class TestIdentityVerificationEndpoint:
    """Validates pre-exam photo ID and live selfie biometric verification."""

    def test_identity_verify_success(self, client):
        doc_b64 = create_dummy_base64_image((120, 120, 120))
        selfie_b64 = create_dummy_base64_image((120, 120, 120))

        payload = {
            "candidate_id": "CANDIDATE_001",
            "document_image_b64": doc_b64,
            "selfie_image_b64": selfie_b64,
            "document_type": "PASSPORT"
        }

        response = client.post("/api/v1/identity/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_id"] == "CANDIDATE_001"
        assert "status" in data
        assert "match_confidence" in data
        assert data["document_type"] == "PASSPORT"

    def test_identity_verify_corrupted_payload(self, client):
        payload = {
            "candidate_id": "CANDIDATE_BAD",
            "document_image_b64": "not_a_valid_base64_string",
            "selfie_image_b64": "also_invalid",
            "document_type": "DRIVERS_LICENSE"
        }
        response = client.post("/api/v1/identity/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert data["verified"] is False


class TestCandidateSessionLifecycle:
    """Validates starting sessions, sending frames, and fetching candidate status."""

    def test_session_start_and_status(self, client):
        start_payload = {
            "candidate_id": "STUDENT_99",
            "exam_id": "CS101_FINAL"
        }
        resp_start = client.post("/api/v1/sessions/start", json=start_payload)
        assert resp_start.status_code == 200
        start_data = resp_start.json()
        sess_id = start_data["session_id"]
        assert start_data["candidate_id"] == "STUDENT_99"
        assert start_data["status"] == "ACTIVE"
        assert start_data["cumulative_risk_score"] == 0.0

        # Fetch status
        resp_stat = client.get(f"/api/v1/sessions/{sess_id}/status")
        assert resp_stat.status_code == 200
        stat_data = resp_stat.json()
        assert stat_data["session_id"] == sess_id
        assert stat_data["status"] == "ACTIVE"

    def test_session_status_not_found(self, client):
        resp = client.get("/api/v1/sessions/non_existent_sess/status")
        assert resp.status_code == 404

    def test_frame_submission_and_orchestration_cycle(self, client):
        # 1. Start session
        start_payload = {
            "candidate_id": "STUDENT_STREAM",
            "exam_id": "MATH301",
            "session_id": "sess_stream_01"
        }
        client.post("/api/v1/sessions/start", json=start_payload)

        # 2. Submit frame with suspicious transcript
        frame_b64 = create_dummy_base64_image()
        frame_payload = {
            "primary_frame_b64": frame_b64,
            "audio_transcript": "Can you tell me the answer to question number three?"
        }

        resp_frame = client.post("/api/v1/sessions/sess_stream_01/frames", json=frame_payload)
        assert resp_frame.status_code == 200
        frame_data = resp_frame.json()
        assert frame_data["session_id"] == "sess_stream_01"
        assert frame_data["risk_score_delta"] > 0.0
        assert frame_data["cumulative_risk_score"] > 0.0
        assert "orchestrator_decision" in frame_data

    def test_session_evidence_endpoint(self, client):
        resp = client.get("/api/v1/sessions/sess_stream_01/evidence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "sess_stream_01"
        assert "evidence_frames" in data

    def test_session_messaging_and_ack(self, client):
        # Send proctor warning message
        msg_payload = {
            "sender": "PROCTOR",
            "text": "Please adjust your camera angle.",
            "severity": "WARNING"
        }
        resp = client.post("/api/v1/sessions/sess_stream_01/messages", json=msg_payload)
        assert resp.status_code == 200
        msg_data = resp.json()
        assert msg_data["sender"] == "PROCTOR"
        assert msg_data["text"] == "Please adjust your camera angle."
        assert msg_data["severity"] == "WARNING"
        msg_id = msg_data["message_id"]

        # Fetch messages list
        resp_list = client.get("/api/v1/sessions/sess_stream_01/messages")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert len(list_data["messages"]) >= 1

        # Candidate acknowledges message
        resp_ack = client.post(f"/api/v1/sessions/sess_stream_01/messages/{msg_id}/ack")
        assert resp_ack.status_code == 200
        assert resp_ack.json()["status"] == "ACKNOWLEDGED"


class TestProctorReviewPortal:
    """Validates proctor dashboard endpoints, audit timelines, and human actions."""

    def test_list_proctor_sessions(self, client):
        # Seed an active session
        client.post("/api/v1/sessions/start", json={
            "candidate_id": "CANDIDATE_LIST_TEST",
            "exam_id": "PHYS101",
            "session_id": "sess_list_01"
        })

        resp = client.get("/api/v1/proctor/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_active_sessions"] >= 1
        sess_ids = [s["session_id"] for s in data["sessions"]]
        assert "sess_list_01" in sess_ids

    def test_get_session_timeline(self, client):
        sess_id = "sess_timeline_01"
        client.post("/api/v1/sessions/start", json={
            "candidate_id": "CANDIDATE_TIMELINE",
            "exam_id": "CHEM101",
            "session_id": sess_id
        })

        # Ingest a frame to populate timeline
        client.post(f"/api/v1/sessions/{sess_id}/frames", json={
            "audio_transcript": "Hey proctor, testing question."
        })

        resp = client.get(f"/api/v1/proctor/sessions/{sess_id}/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_summary" in data
        assert "timeline" in data
        assert data["session_summary"]["session_id"] == sess_id

    def test_proctor_manual_actions(self, client):
        sess_id = "sess_proctor_action_01"
        client.post("/api/v1/sessions/start", json={
            "candidate_id": "CANDIDATE_ACTION",
            "exam_id": "ENG101",
            "session_id": sess_id
        })

        # 1. Issue Warning
        warn_payload = {
            "proctor_id": "PROCTOR_SMITH",
            "action": "ISSUE_WARNING",
            "notes": "Candidate instructed to center face in frame."
        }
        resp_warn = client.post(f"/api/v1/proctor/sessions/{sess_id}/decision", json=warn_payload)
        assert resp_warn.status_code == 200
        assert resp_warn.json()["warning_count"] == 1
        assert resp_warn.json()["action_applied"] == "ISSUE_WARNING"

        # 2. Terminate Session
        term_payload = {
            "proctor_id": "PROCTOR_SMITH",
            "action": "TERMINATE_SESSION",
            "notes": "Severe repeated collusion detected."
        }
        resp_term = client.post(f"/api/v1/proctor/sessions/{sess_id}/decision", json=term_payload)
        assert resp_term.status_code == 200
        assert resp_term.json()["new_status"] == "TERMINATED"

        # Verify candidate status reflects termination
        resp_status = client.get(f"/api/v1/sessions/{sess_id}/status")
        assert resp_status.json()["status"] == "TERMINATED"


class TestProctorWebSocketAlertStream:
    """Validates real-time WebSocket connection for proctor dashboard."""

    def test_websocket_connection_and_ping(self, client):
        with client.websocket_connect("/api/v1/proctor/stream") as ws:
            # 1. Expect greeting
            greeting = ws.receive_json()
            assert greeting["type"] == "CONNECTION_ESTABLISHED"
            assert "active_sessions_count" in greeting

            # 2. Ping-Pong test
            ws.send_text("PING")
            pong = ws.receive_text()
            assert pong == "PONG"
