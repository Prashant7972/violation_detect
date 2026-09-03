import base64
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def generate_synthetic_base64_frame():
    # Create a 640x480 black image with a blue circle
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(img, (320, 240), 50, (255, 0, 0), -1)
    _, buffer = cv2.imencode('.jpg', img)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"

def test_session_lifecycle_and_frame_processing():
    # 1. Create Session
    response = client.post("/api/v1/sessions", json={"user_id": "test-user-1"})
    assert response.status_code == 201
    data = response.json()
    session_id = data["session_id"]
    assert data["status"] == "ACTIVE"
    assert data["user_id"] == "test-user-1"

    # 2. Submit Frame Payload
    frame_b64 = generate_synthetic_base64_frame()
    frame_response = client.post(
        f"/api/v1/sessions/{session_id}/frames",
        json={
            "session_id": session_id,
            "timestamp": "2026-09-03T10:00:00Z",
            "frame_data": frame_b64
        }
    )
    assert frame_response.status_code == 200
    frame_data = frame_response.json()
    assert "status" in frame_data

    # 3. Query Session Events
    events_response = client.get(f"/api/v1/sessions/{session_id}/events")
    assert events_response.status_code == 200
    events_data = events_response.json()
    assert events_data["session_id"] == session_id

    # 4. End Session
    end_response = client.post(f"/api/v1/sessions/{session_id}/end")
    assert end_response.status_code == 200
    assert end_response.json()["status"] == "COMPLETED"
