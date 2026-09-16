"""
Candidate Session Lifecycle Endpoints (API v1)
Handles session initialization, continuous frame ingestion, and real-time proctoring status.
"""

import base64
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.state import ProctorSessionState
from src.features.proctor_orchestrator.graph import proctoring_graph
from src.features.media_ingestion.schemas import CameraSource, FrameIngestPayload
from src.features.media_ingestion.stream_handler import stream_handler

logger = logging.getLogger("sessions_api")

import os
import cv2
import time
import uuid
import numpy as np

router = APIRouter(prefix="/sessions", tags=["Candidate Sessions"])

# In-memory registries for active exams, stored evidence, and live messaging
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_EVIDENCE: Dict[str, List[Dict[str, Any]]] = {}
SESSION_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}


class SessionStartRequest(BaseModel):
    candidate_id: str = Field(..., description="Student or candidate identifier")
    exam_id: str = Field(default="DEFAULT_EXAM", description="Exam / Assessment code")
    session_id: Optional[str] = Field(default=None, description="Optional custom session UUID")


class SessionStartResponse(BaseModel):
    session_id: str
    candidate_id: str
    exam_id: str
    started_at: str
    status: str = "ACTIVE"
    cumulative_risk_score: float = 0.0


class FrameSubmissionRequest(BaseModel):
    timestamp: Optional[str] = None
    primary_frame_b64: Optional[str] = None
    secondary_frame_b64: Optional[str] = None
    audio_chunk_b64: Optional[str] = None
    audio_transcript: Optional[str] = None


class FrameSubmissionResponse(BaseModel):
    session_id: str
    timestamp: str
    risk_score_delta: float
    cumulative_risk_score: float
    orchestrator_decision: str
    warning_count: int
    new_violations_count: int
    new_evidence_count: int
    requires_human_triage: bool
    violations: List[str] = Field(default_factory=list)
    evidence_url: Optional[str] = None
    summary_message: Optional[str] = None


class SessionMessagePayload(BaseModel):
    sender: str = Field(..., description="'PROCTOR' or 'CANDIDATE'")
    text: str = Field(..., description="Message text")
    severity: Optional[str] = Field(default="INFO", description="'INFO', 'WARNING', or 'CRITICAL'")


class SessionMessageItem(BaseModel):
    message_id: str
    session_id: str
    sender: str
    text: str
    severity: str
    timestamp: str
    acknowledged: bool = False


@router.post("/start", response_model=SessionStartResponse)
def start_candidate_session(payload: SessionStartRequest):
    """Initializes a new continuous proctored examination session."""
    now_iso = datetime.now(timezone.utc).isoformat()
    sess_id = payload.session_id or f"sess_{payload.candidate_id}_{int(datetime.now().timestamp())}"

    session_record = {
        "session_id": sess_id,
        "candidate_id": payload.candidate_id,
        "exam_id": payload.exam_id,
        "started_at": now_iso,
        "status": "ACTIVE",
        "cumulative_risk_score": 0.0,
        "warning_count": 0,
        "latest_decision": "CONTINUE"
    }
    ACTIVE_SESSIONS[sess_id] = session_record

    return SessionStartResponse(
        session_id=sess_id,
        candidate_id=payload.candidate_id,
        exam_id=payload.exam_id,
        started_at=now_iso,
        status="ACTIVE",
        cumulative_risk_score=0.0
    )


@router.post("/{session_id}/frames", response_model=FrameSubmissionResponse)
def submit_session_frames(session_id: str, payload: FrameSubmissionRequest):
    """
    Submits primary camera frame and optional secondary mobile camera frame.
    Executes a LangGraph orchestration cycle and returns updated proctoring evaluation.
    """
    if session_id not in ACTIVE_SESSIONS:
        # Auto-provision if not explicitly started
        ACTIVE_SESSIONS[session_id] = {
            "session_id": session_id,
            "candidate_id": "CANDIDATE",
            "exam_id": "EXAM",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "ACTIVE"
        }

    candidate_id = ACTIVE_SESSIONS[session_id]["candidate_id"]
    timestamp = payload.timestamp or datetime.now(timezone.utc).isoformat()

    # Decode primary frame bytes
    p_bytes = None
    if payload.primary_frame_b64:
        try:
            b64_str = payload.primary_frame_b64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            p_bytes = base64.b64decode(b64_str)
        except Exception as e:
            logger.error(f"Error decoding primary frame: {e}")

    # Decode secondary frame bytes
    s_bytes = None
    if payload.secondary_frame_b64:
        try:
            b64_str = payload.secondary_frame_b64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            s_bytes = base64.b64decode(b64_str)
        except Exception as e:
            logger.error(f"Error decoding secondary frame: {e}")

    # Build input state for LangGraph step
    step_state: ProctorSessionState = {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "timestamp": timestamp,
        "primary_frame_bytes": p_bytes,
        "secondary_frame_bytes": s_bytes,
        "audio_chunk_bytes": None,
        "audio_transcript": payload.audio_transcript,
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

    # Execute LangGraph state transition with checkpointer thread_id
    evaluated_state = proctoring_graph.invoke(
        step_state,
        config={"configurable": {"thread_id": session_id}}
    )

    cum_score = evaluated_state.get("cumulative_risk_score", 0.0)
    decision = evaluated_state.get("orchestrator_decision", "CONTINUE")
    warn_count = evaluated_state.get("warning_count", 0)
    step_violations = evaluated_state.get("step_violations", [])
    violation_ids = [v.get("violation_id", "POLICY_BREACH") for v in step_violations]

    # Stored violation evidence keyframes persistence
    evidence_url = None
    if step_violations and p_bytes:
        try:
            from app.ai.detector import AIDetector
            evidence_base = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "evidence"))
            session_ev_dir = os.path.join(evidence_base, "candidates", session_id)
            os.makedirs(session_ev_dir, exist_ok=True)
            
            nparr = np.frombuffer(p_bytes, np.uint8)
            frame_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame_img is not None:
                flagged_boxes = []
                for v in step_violations:
                    m = v.get("metadata", {})
                    if "bounding_box" in m and m["bounding_box"]:
                        flagged_boxes.append({
                            "object": m.get("name", "violation"),
                            "bounding_box": m["bounding_box"],
                            "confidence": m.get("confidence", 0.90)
                        })
                
                annotated = AIDetector.annotate_frame(frame_img, flagged_boxes) if flagged_boxes else frame_img
                ts_clean = int(time.time() * 1000)
                v_tag = violation_ids[0].lower() if violation_ids else "violation"
                filename = f"live_evidence_{v_tag}_{ts_clean}.jpg"
                save_path = os.path.join(session_ev_dir, filename)
                cv2.imwrite(save_path, annotated)
                evidence_url = f"/evidence/candidates/{session_id}/{filename}"
                
                ev_record = {
                    "evidence_id": f"ev_{ts_clean}",
                    "timestamp": timestamp,
                    "violation_type": violation_ids[0] if violation_ids else "VIOLATION",
                    "severity": step_violations[0].get("severity", "HIGH"),
                    "evidence_url": evidence_url,
                    "details": step_violations[0].get("details", "AI proctoring policy violation detected.")
                }
                if session_id not in SESSION_EVIDENCE:
                    SESSION_EVIDENCE[session_id] = []
                SESSION_EVIDENCE[session_id].append(ev_record)
        except Exception as ev_err:
            logger.warning(f"Error persisting violation evidence frame: {ev_err}")

    summary_msg = "Clean frame" if not violation_ids else f"Violations detected: {', '.join(violation_ids)}"

    # Update active registry
    ACTIVE_SESSIONS[session_id]["cumulative_risk_score"] = cum_score
    ACTIVE_SESSIONS[session_id]["latest_decision"] = decision
    ACTIVE_SESSIONS[session_id]["warning_count"] = warn_count

    return FrameSubmissionResponse(
        session_id=session_id,
        timestamp=timestamp,
        risk_score_delta=evaluated_state.get("risk_score_delta", 0.0),
        cumulative_risk_score=cum_score,
        orchestrator_decision=decision,
        warning_count=warn_count,
        new_violations_count=len(step_violations),
        new_evidence_count=len(evaluated_state.get("evidence_events", [])),
        requires_human_triage=decision in ["ESCALATE_HUMAN", "TERMINATE"],
        violations=violation_ids,
        evidence_url=evidence_url,
        summary_message=summary_msg
    )


@router.get("/{session_id}/evidence")
def get_session_evidence(session_id: str):
    """Returns stored violation evidence keyframes for candidate and proctor review."""
    return {
        "session_id": session_id,
        "evidence_frames": SESSION_EVIDENCE.get(session_id, [])
    }


@router.post("/{session_id}/messages", response_model=SessionMessageItem)
def send_session_message(session_id: str, payload: SessionMessagePayload):
    """Direct live communication between human proctor and candidate."""
    if session_id not in SESSION_MESSAGES:
        SESSION_MESSAGES[session_id] = []
    
    msg_id = f"msg_{int(time.time() * 1000)}_{str(uuid.uuid4())[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    msg_item = {
        "message_id": msg_id,
        "session_id": session_id,
        "sender": payload.sender.upper(),
        "text": payload.text.strip(),
        "severity": payload.severity.upper() if payload.severity else "INFO",
        "timestamp": now_iso,
        "acknowledged": False
    }
    SESSION_MESSAGES[session_id].append(msg_item)
    return SessionMessageItem(**msg_item)


@router.get("/{session_id}/messages")
def get_session_messages(session_id: str):
    """Retrieves all chat messages and warnings for this proctoring session."""
    return {
        "session_id": session_id,
        "messages": SESSION_MESSAGES.get(session_id, [])
    }


@router.post("/{session_id}/messages/{message_id}/ack")
def acknowledge_session_message(session_id: str, message_id: str):
    """Candidate acknowledges proctor warning or instruction."""
    msgs = SESSION_MESSAGES.get(session_id, [])
    for m in msgs:
        if m["message_id"] == message_id:
            m["acknowledged"] = True
            return {"status": "ACKNOWLEDGED", "message_id": message_id}
    return {"status": "NOT_FOUND", "message_id": message_id}


@router.get("/{session_id}/status")
def get_session_status(session_id: str):
    """Returns current active risk metrics and proctoring status for a candidate session."""
    if session_id not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found."
        )
    return ACTIVE_SESSIONS[session_id]
