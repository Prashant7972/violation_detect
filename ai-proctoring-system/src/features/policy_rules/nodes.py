"""
Policy Rules and RAG Evaluator LangGraph Node
Cross-references visual, object, and acoustic signals against institutional proctoring policies.
"""

import logging
from typing import Dict, Any, List

from src.core.state import ProctorSessionState
from src.features.policy_rules.retriever import policy_retriever
from src.features.policy_rules.schemas import PolicyViolation
from src.features.vision_proctoring.schemas import AnomalySeverity

logger = logging.getLogger("policy_rules_node")


def policy_evaluation_node(state: ProctorSessionState) -> Dict[str, Any]:
    """
    LangGraph node for policy evaluation.
    Screens all anomalies and detected hardware against institutional rules,
    producing an immutable list of policy violations with assigned severity and penalties.
    
    Returns partial state update:
        policy_violations: List[Dict[str, Any]] (appends to accumulator)
        step_violations: List[Dict[str, Any]] (current frame violations for risk delta calculation)
    """
    detected_objects = state.get("detected_objects", [])
    visual_anomalies = state.get("visual_anomalies", [])
    audio_anomalies = state.get("audio_anomalies", [])
    timestamp = state.get("timestamp", "UNKNOWN_TIMESTAMP")
    session_id = state.get("session_id", "UNKNOWN_SESSION")

    violations: List[Dict[str, Any]] = []

    # 1. Evaluate Detected Objects against Strictly Prohibited List
    for obj in detected_objects:
        obj_name = obj.get("name", "unknown")
        confidence = float(obj.get("confidence", 0.90))

        if policy_retriever.is_object_prohibited(obj_name):
            severity = AnomalySeverity.CRITICAL
            penalty = policy_retriever.get_penalty_points(severity)
            
            violation = PolicyViolation(
                violation_id="PROHIBITED_DEVICE_DETECTED",
                rule_category="HARDWARE",
                severity=severity,
                confidence=confidence,
                details=f"Candidate was detected with prohibited device: {obj_name} (confidence: {confidence:.2f})",
                timestamp=timestamp,
                source_detection="PRIMARY_WEBCAM",
                penalty_points=penalty,
                metadata=obj
            )
            violations.append(violation.model_dump())

    # 2. Evaluate Visual Anomalies (Face Absence, Secondary Individuals, Gaze)
    for vanom in visual_anomalies:
        atype = vanom.get("type", "")
        # Avoid duplicate logging if already recorded as prohibited hardware
        if atype == "PROHIBITED_HARDWARE_DETECTED":
            continue

        if atype in ["NO_FACE_DETECTED", "MULTIPLE_FACES_DETECTED", "SUSPICIOUS_GAZE"]:
            severity = policy_retriever.get_severity_for_anomaly(atype)
            penalty = policy_retriever.get_penalty_points(severity)

            violation = PolicyViolation(
                violation_id=atype,
                rule_category="IDENTITY" if "FACE" in atype else "GAZE",
                severity=severity,
                confidence=0.92,
                details=vanom.get("details", f"Visual policy anomaly: {atype}"),
                timestamp=timestamp,
                source_detection="PRIMARY_WEBCAM",
                penalty_points=penalty,
                metadata=vanom
            )
            violations.append(violation.model_dump())

    # 3. Evaluate Audio Anomalies (Whispering, Dictation, Multiple Voices)
    for aanom in audio_anomalies:
        atype = aanom.get("type", "")
        if atype in [
            "WHISPERING_DETECTED",
            "DICTATION_OR_COLLUSION_DETECTED",
            "MULTIPLE_VOICES_DETECTED"
        ]:
            severity = policy_retriever.get_severity_for_anomaly(atype)
            penalty = policy_retriever.get_penalty_points(severity)

            violation = PolicyViolation(
                violation_id=atype,
                rule_category="ACOUSTIC",
                severity=severity,
                confidence=float(aanom.get("confidence", 0.90)),
                details=aanom.get("details", f"Acoustic policy breach: {atype}"),
                timestamp=timestamp,
                source_detection="AUDIO",
                penalty_points=penalty,
                metadata=aanom
            )
            violations.append(violation.model_dump())

    return {
        "policy_violations": violations,
        "step_violations": violations
    }
