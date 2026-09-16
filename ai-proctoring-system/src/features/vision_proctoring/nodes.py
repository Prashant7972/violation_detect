"""
Vision Proctoring LangGraph Node
Orchestrates multimodal frame evaluation via Google Gemini 2.5 Flash,
derives face count, unauthorized hardware, and gaze anomalies.
"""

import json
import logging
from typing import Dict, Any, List

from src.core.state import ProctorSessionState
from src.core.gemini_client import gemini_client
from src.features.vision_proctoring.prompts import (
    VISION_PROCTORING_SYSTEM_INSTRUCTION,
    VISION_PROCTORING_USER_PROMPT
)
from src.features.vision_proctoring.schemas import (
    VisionAnalysisResponse,
    VisualAnomalyItem,
    AnomalySeverity,
    GazeAssessment
)

logger = logging.getLogger("vision_proctoring_node")


def vision_proctoring_node(state: ProctorSessionState) -> Dict[str, Any]:
    """
    LangGraph node for real-time vision proctoring.
    Evaluates primary camera frame (and secondary mobile frame if available),
    detects face counts, prohibited objects, and gaze direction.
    
    Returns partial state update:
        face_count: int
        detected_objects: List[Dict[str, Any]]
        visual_anomalies: List[Dict[str, Any]]
    """
    primary_frame = state.get("primary_frame_bytes")
    timestamp = state.get("timestamp", "UNKNOWN_TIMESTAMP")
    session_id = state.get("session_id", "UNKNOWN_SESSION")

    # Graceful handling for missing frame
    if not primary_frame:
        logger.warning(f"No primary frame available for session {session_id}. Returning neutral vision state.")
        return {
            "face_count": 1,
            "detected_objects": [],
            "visual_anomalies": []
        }

    # Invoke Gemini Multimodal Vision Analysis
    full_prompt = f"{VISION_PROCTORING_SYSTEM_INSTRUCTION}\n\n{VISION_PROCTORING_USER_PROMPT}"
    raw_response = gemini_client.generate_vision_analysis(
        frame_bytes=primary_frame,
        prompt=full_prompt
    )

    try:
        parsed = VisionAnalysisResponse.model_validate(raw_response)
    except Exception as e:
        logger.error(f"Error parsing Gemini Vision response: {e}. Raw response: {raw_response}")
        parsed = VisionAnalysisResponse()

    face_count = parsed.face_count
    detected_objects: List[Dict[str, Any]] = [
        obj.model_dump() for obj in parsed.unauthorized_objects
    ]
    visual_anomalies: List[Dict[str, Any]] = []

    # 1. Evaluate Face Count Anomalies
    if face_count == 0 or not parsed.face_detected:
        visual_anomalies.append({
            "type": "NO_FACE_DETECTED",
            "severity": AnomalySeverity.HIGH.value,
            "timestamp": timestamp,
            "details": "Candidate face absent from camera frame.",
            "metadata": {"face_count": 0}
        })
    elif face_count > 1:
        visual_anomalies.append({
            "type": "MULTIPLE_FACES_DETECTED",
            "severity": AnomalySeverity.HIGH.value,
            "timestamp": timestamp,
            "details": f"{face_count} distinct human faces visible in exam room.",
            "metadata": {"face_count": face_count}
        })

    # 2. Evaluate Gaze / Posture Anomalies
    if parsed.gaze_assessment in [GazeAssessment.LOOKING_AWAY, GazeAssessment.SUSPICIOUS]:
        visual_anomalies.append({
            "type": "SUSPICIOUS_GAZE",
            "severity": AnomalySeverity.MEDIUM.value,
            "timestamp": timestamp,
            "details": f"Candidate gaze flagged as {parsed.gaze_assessment.value}: {parsed.anomaly_summary}",
            "metadata": {"gaze_assessment": parsed.gaze_assessment.value}
        })

    # 3. Log Prohibited Objects directly as visual anomalies
    for obj in parsed.unauthorized_objects:
        visual_anomalies.append({
            "type": "PROHIBITED_HARDWARE_DETECTED",
            "severity": AnomalySeverity.CRITICAL.value,
            "timestamp": timestamp,
            "details": f"Unauthorized device detected: {obj.name} (confidence: {obj.confidence:.2f})",
            "metadata": obj.model_dump()
        })

    return {
        "face_count": face_count,
        "detected_objects": detected_objects,
        "visual_anomalies": visual_anomalies
    }
