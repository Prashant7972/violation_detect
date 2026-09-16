"""
Unit Tests for Vision Proctoring Node (Step 3)
"""

import sys
import os
import cv2
import pytest
import numpy as np

# Add src to sys.path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.state import ProctorSessionState
from src.core.gemini_client import gemini_client
from src.features.vision_proctoring.nodes import vision_proctoring_node
from src.features.vision_proctoring.schemas import GazeAssessment


def create_dummy_frame_bytes() -> bytes:
    """Helper to create dummy JPEG bytes."""
    frame = np.full((240, 320, 3), 150, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes()


def build_base_state(frame_bytes=None) -> ProctorSessionState:
    """Helper to construct baseline ProctorSessionState."""
    return {
        "session_id": "sess_vision_001",
        "candidate_id": "cand_vision_001",
        "timestamp": "2026-09-15T10:00:00Z",
        "primary_frame_bytes": frame_bytes or create_dummy_frame_bytes(),
        "secondary_frame_bytes": None,
        "audio_chunk_bytes": None,
        "audio_transcript": None,
        "face_count": 0,
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


def test_vision_node_normal_forward_gaze(monkeypatch):
    """Verifies that a normal candidate facing forward produces zero anomalies."""
    mock_resp = {
        "face_count": 1,
        "face_detected": True,
        "unauthorized_objects": [],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Candidate observed facing exam screen normally."
    }
    monkeypatch.setattr(gemini_client, "generate_vision_analysis", lambda frame_bytes, prompt: mock_resp)

    state = build_base_state()
    result = vision_proctoring_node(state)

    assert result["face_count"] == 1
    assert len(result["detected_objects"]) == 0
    assert len(result["visual_anomalies"]) == 0


def test_vision_node_no_face_detected(monkeypatch):
    """Verifies that absence of a face triggers NO_FACE_DETECTED anomaly with HIGH severity."""
    mock_resp = {
        "face_count": 0,
        "face_detected": False,
        "unauthorized_objects": [],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Candidate not present at desk."
    }
    monkeypatch.setattr(gemini_client, "generate_vision_analysis", lambda frame_bytes, prompt: mock_resp)

    state = build_base_state()
    result = vision_proctoring_node(state)

    assert result["face_count"] == 0
    assert len(result["visual_anomalies"]) == 1
    anomaly = result["visual_anomalies"][0]
    assert anomaly["type"] == "NO_FACE_DETECTED"
    assert anomaly["severity"] == "HIGH"


def test_vision_node_multiple_faces_detected(monkeypatch):
    """Verifies that presence of extra individuals triggers MULTIPLE_FACES_DETECTED with HIGH severity."""
    mock_resp = {
        "face_count": 2,
        "face_detected": True,
        "unauthorized_objects": [],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Two people observed in the room."
    }
    monkeypatch.setattr(gemini_client, "generate_vision_analysis", lambda frame_bytes, prompt: mock_resp)

    state = build_base_state()
    result = vision_proctoring_node(state)

    assert result["face_count"] == 2
    assert len(result["visual_anomalies"]) == 1
    anomaly = result["visual_anomalies"][0]
    assert anomaly["type"] == "MULTIPLE_FACES_DETECTED"
    assert anomaly["severity"] == "HIGH"


def test_vision_node_suspicious_gaze(monkeypatch):
    """Verifies that persistent looking away triggers SUSPICIOUS_GAZE anomaly with MEDIUM severity."""
    mock_resp = {
        "face_count": 1,
        "face_detected": True,
        "unauthorized_objects": [],
        "gaze_assessment": "LOOKING_AWAY",
        "anomaly_summary": "Candidate repeatedly glancing toward the right corner."
    }
    monkeypatch.setattr(gemini_client, "generate_vision_analysis", lambda frame_bytes, prompt: mock_resp)

    state = build_base_state()
    result = vision_proctoring_node(state)

    assert len(result["visual_anomalies"]) == 1
    anomaly = result["visual_anomalies"][0]
    assert anomaly["type"] == "SUSPICIOUS_GAZE"
    assert anomaly["severity"] == "MEDIUM"


def test_vision_node_prohibited_device_detected(monkeypatch):
    """Verifies that a visible smartphone is extracted into detected_objects and visual_anomalies with CRITICAL severity."""
    mock_resp = {
        "face_count": 1,
        "face_detected": True,
        "unauthorized_objects": [
            {
                "name": "smartphone",
                "confidence": 0.94,
                "bounding_box": [320, 110, 480, 240]
            }
        ],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Candidate holding a smartphone in their hand."
    }
    monkeypatch.setattr(gemini_client, "generate_vision_analysis", lambda frame_bytes, prompt: mock_resp)

    state = build_base_state()
    result = vision_proctoring_node(state)

    assert len(result["detected_objects"]) == 1
    obj = result["detected_objects"][0]
    assert obj["name"] == "smartphone"
    assert obj["confidence"] == 0.94

    assert len(result["visual_anomalies"]) == 1
    anomaly = result["visual_anomalies"][0]
    assert anomaly["type"] == "PROHIBITED_HARDWARE_DETECTED"
    assert anomaly["severity"] == "CRITICAL"


def test_vision_node_missing_frame_graceful_handling():
    """Verifies that passing None for primary frame does not fail the graph and returns neutral state."""
    state = build_base_state(frame_bytes=None)
    state["primary_frame_bytes"] = None

    result = vision_proctoring_node(state)
    assert result["face_count"] == 1
    assert len(result["detected_objects"]) == 0
    assert len(result["visual_anomalies"]) == 0
