"""
Unit Tests for LangGraph Proctor Orchestrator StateGraph (Step 6)
Verifies Acceptance Criteria 1, 2, 3, and 4 from the project specification.
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
from src.features.proctor_orchestrator.graph import (
    build_proctoring_graph,
    MemorySaver,
    ProctorStateGraphEngine
)


def create_dummy_jpeg() -> bytes:
    """Helper to generate dummy JPEG bytes."""
    frame = np.full((200, 200, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes()


def build_test_state(session_id="sess_graph_001", candidate_id="cand_001", frame_bytes=None) -> ProctorSessionState:
    """Helper to create test ProctorSessionState."""
    return {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "timestamp": "2026-09-15T10:15:00Z",
        "primary_frame_bytes": frame_bytes or create_dummy_jpeg(),
        "secondary_frame_bytes": None,
        "audio_chunk_bytes": None,
        "audio_transcript": None,
        "face_count": 1,
        "face_matched": True,
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


def test_acceptance_criteria_1_prohibited_device_produces_critical_violation_and_evidence(monkeypatch):
    """
    Acceptance Criteria 1:
    Given a sample frame with a visible smartphone, the graph produces a
    PROHIBITED_DEVICE policy violation and an evidence_events entry with severity: CRITICAL.
    """
    mock_resp = {
        "face_count": 1,
        "face_detected": True,
        "unauthorized_objects": [
            {"name": "smartphone", "confidence": 0.96, "bounding_box": [100, 100, 200, 200]}
        ],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Candidate holding a smartphone."
    }
    monkeypatch.setattr(
        gemini_client,
        "generate_vision_analysis",
        lambda *args, **kwargs: mock_resp
    )

    graph = build_proctoring_graph()
    state = build_test_state()

    result = graph.invoke(state, config={"configurable": {"thread_id": state["session_id"]}})

    # Check policy violation
    violations = result["policy_violations"]
    assert any(v["violation_id"] == "PROHIBITED_DEVICE_DETECTED" for v in violations)
    prohibited_v = next(v for v in violations if v["violation_id"] == "PROHIBITED_DEVICE_DETECTED")
    assert prohibited_v["severity"] == "CRITICAL"

    # Check evidence event
    events = result["evidence_events"]
    assert len(events) >= 1
    crit_event = next(e for e in events if e["severity"] == "CRITICAL")
    assert crit_event["policy_rule_triggered"] == "PROHIBITED_DEVICE_DETECTED"
    assert result["orchestrator_decision"] == "ESCALATE_HUMAN"


def test_acceptance_criteria_2_face_absence_and_multiple_faces(monkeypatch):
    """
    Acceptance Criteria 2:
    Given a frame with zero or multiple faces, visual_anomalies correctly flags
    NO_FACE_DETECTED / MULTIPLE_FACES_DETECTED.
    """
    # 1. Zero faces
    zero_resp = {
        "face_count": 0,
        "face_detected": False,
        "unauthorized_objects": [],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "No face"
    }
    monkeypatch.setattr(
        gemini_client,
        "generate_vision_analysis",
        lambda *args, **kwargs: zero_resp
    )
    graph = build_proctoring_graph()
    res_zero = graph.invoke(build_test_state(), config={"configurable": {"thread_id": "test_zero"}})
    assert any(a["type"] == "NO_FACE_DETECTED" for a in res_zero["visual_anomalies"])

    # 2. Multiple faces
    multi_resp = {
        "face_count": 2,
        "face_detected": True,
        "unauthorized_objects": [],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Two people"
    }
    monkeypatch.setattr(
        gemini_client,
        "generate_vision_analysis",
        lambda *args, **kwargs: multi_resp
    )
    res_multi = graph.invoke(build_test_state(), config={"configurable": {"thread_id": "test_multi"}})
    assert any(a["type"] == "MULTIPLE_FACES_DETECTED" for a in res_multi["visual_anomalies"])


def test_acceptance_criteria_3_cumulative_risk_accumulates_and_clamps_at_100(monkeypatch):
    """
    Acceptance Criteria 3:
    cumulative_risk_score correctly accumulates and clamps at 100.0 across multiple
    graph invocations for the same session_id (verifying checkpointer state retention).
    """
    # Mock high violation producing 35 penalty points each invocation
    mock_resp = {
        "face_count": 1,
        "face_detected": True,
        "unauthorized_objects": [{"name": "smartphone", "confidence": 0.95}],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Phone visible"
    }
    monkeypatch.setattr(
        gemini_client,
        "generate_vision_analysis",
        lambda *args, **kwargs: mock_resp
    )

    checkpointer = MemorySaver()
    graph = build_proctoring_graph(checkpointer=checkpointer)
    session_id = "sess_accumulate_test"
    config = {"configurable": {"thread_id": session_id}}

    # Step 1: 0 -> 35
    state1 = build_test_state(session_id=session_id)
    out1 = graph.invoke(state1, config=config)
    assert out1["cumulative_risk_score"] == 35.0

    # Step 2: 35 -> 70
    state2 = build_test_state(session_id=session_id)
    out2 = graph.invoke(state2, config=config)
    assert out2["cumulative_risk_score"] == 70.0

    # Step 3: 70 -> 100 (clamped from 105)
    state3 = build_test_state(session_id=session_id)
    out3 = graph.invoke(state3, config=config)
    assert out3["cumulative_risk_score"] == 100.0

    # Step 4: Stays clamped at 100.0
    state4 = build_test_state(session_id=session_id)
    out4 = graph.invoke(state4, config=config)
    assert out4["cumulative_risk_score"] == 100.0


def test_acceptance_criteria_4_human_oversight_guarantee(monkeypatch):
    """
    Acceptance Criteria 4:
    orchestrator_decision of ESCALATE_HUMAN or TERMINATE is never auto-executed
    against the candidate — it always surfaces to the Proctor Review Portal pending human confirmation.
    """
    mock_resp = {
        "face_count": 1,
        "face_detected": True,
        "unauthorized_objects": [{"name": "smartphone", "confidence": 0.99}],
        "gaze_assessment": "FORWARD",
        "anomaly_summary": "Active phone usage"
    }
    monkeypatch.setattr(
        gemini_client,
        "generate_vision_analysis",
        lambda *args, **kwargs: mock_resp
    )

    graph = build_proctoring_graph()
    state = build_test_state(session_id="sess_oversight_test")
    result = graph.invoke(state, config={"configurable": {"thread_id": state["session_id"]}})

    # Verify decision routed to human review
    assert result["orchestrator_decision"] in ["ESCALATE_HUMAN", "TERMINATE"]
    events = result["evidence_events"]
    assert len(events) >= 1
    # Check human triage status guarantee
    for ev in events:
        assert ev["system_action"] == "FLAGGED_FOR_HUMAN_TRIAGE"
        assert ev["proctor_review_status"] == "PENDING_VERIFICATION"
