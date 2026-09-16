"""
Unit Tests for Policy Rules & Evaluator Feature (Step 5)
"""

import sys
import os
import pytest

# Add src to sys.path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.state import ProctorSessionState
from src.features.policy_rules.retriever import policy_retriever
from src.features.policy_rules.nodes import policy_evaluation_node
from src.features.vision_proctoring.schemas import AnomalySeverity


def build_base_policy_state() -> ProctorSessionState:
    """Helper to construct baseline ProctorSessionState for policy testing."""
    return {
        "session_id": "sess_policy_001",
        "candidate_id": "cand_policy_001",
        "timestamp": "2026-09-15T10:10:00Z",
        "primary_frame_bytes": None,
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


def test_allowed_objects_trigger_no_violations():
    """Verifies that permitted items (eyeglasses, pen, water bottle) do not cause policy breaches."""
    state = build_base_policy_state()
    state["detected_objects"] = [
        {"name": "eyeglasses", "confidence": 0.96},
        {"name": "pen", "confidence": 0.92}
    ]

    result = policy_evaluation_node(state)
    assert len(result["policy_violations"]) == 0


def test_prohibited_device_triggers_critical_violation():
    """Verifies that unauthorized hardware (e.g. smartphone) emits a CRITICAL violation."""
    state = build_base_policy_state()
    state["detected_objects"] = [
        {"name": "smartphone", "confidence": 0.95, "bounding_box": [100, 100, 200, 200]}
    ]

    result = policy_evaluation_node(state)
    assert len(result["policy_violations"]) == 1
    v = result["policy_violations"][0]
    assert v["violation_id"] == "PROHIBITED_DEVICE_DETECTED"
    assert v["severity"] == AnomalySeverity.CRITICAL.value
    assert v["rule_category"] == "HARDWARE"
    assert v["penalty_points"] >= 30.0


def test_visual_anomalies_cross_referenced():
    """Verifies that visual anomalies (NO_FACE, MULTIPLE_FACES) map to HIGH severity policy violations."""
    state = build_base_policy_state()
    state["visual_anomalies"] = [
        {"type": "NO_FACE_DETECTED", "severity": "HIGH", "details": "Face absent"},
        {"type": "MULTIPLE_FACES_DETECTED", "severity": "HIGH", "details": "Second person"}
    ]

    result = policy_evaluation_node(state)
    assert len(result["policy_violations"]) == 2
    types = [v["violation_id"] for v in result["policy_violations"]]
    assert "NO_FACE_DETECTED" in types
    assert "MULTIPLE_FACES_DETECTED" in types


def test_audio_anomalies_cross_referenced():
    """Verifies that acoustic breaches (DICTATION, WHISPERING) map to ACOUSTIC violations."""
    state = build_base_policy_state()
    state["audio_anomalies"] = [
        {
            "type": "DICTATION_OR_COLLUSION_DETECTED",
            "severity": "HIGH",
            "details": "What is the answer spoken aloud",
            "confidence": 0.95
        }
    ]

    result = policy_evaluation_node(state)
    assert len(result["policy_violations"]) == 1
    v = result["policy_violations"][0]
    assert v["violation_id"] == "DICTATION_OR_COLLUSION_DETECTED"
    assert v["rule_category"] == "ACOUSTIC"
    assert v["severity"] == AnomalySeverity.HIGH.value


def test_retriever_is_prohibited_logic():
    """Directly verifies policy retriever classification rules."""
    assert policy_retriever.is_object_prohibited("smartphone") is True
    assert policy_retriever.is_object_prohibited("mobile_phone") is True
    assert policy_retriever.is_object_prohibited("laptop") is True
    assert policy_retriever.is_object_prohibited("apple_watch") is True
    assert policy_retriever.is_object_prohibited("cheat_sheet") is True

    # Permitted items
    assert policy_retriever.is_object_prohibited("eyeglasses") is False
    assert policy_retriever.is_object_prohibited("glasses") is False
    assert policy_retriever.is_object_prohibited("water_bottle") is False
    assert policy_retriever.is_object_prohibited("pen") is False
