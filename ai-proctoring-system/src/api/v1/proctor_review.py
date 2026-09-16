"""
Proctor Review & Human Triage Endpoints (API v1)
Provides proctor dashboard metrics, chronological evidence timeline retrieval,
manual proctor interventions (warnings, terminations, identity approvals),
and real-time WebSocket alert broadcasting.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from pydantic import BaseModel, Field

from src.api.v1.sessions import ACTIVE_SESSIONS
from src.features.proctor_orchestrator.graph import proctoring_graph
from src.features.evidence_reporting.timeline_builder import timeline_builder
from src.features.vision_proctoring.schemas import AnomalySeverity

logger = logging.getLogger("proctor_review_api")

router = APIRouter(prefix="/proctor", tags=["Proctor Review & Triage"])


# =========================================================================
# WebSocket Connection Manager
# =========================================================================

class ProctorStreamManager:
    """Manages active proctor dashboard WebSocket subscriptions."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Proctor client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Proctor client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_alert(self, message: Dict[str, Any]):
        """Broadcasts anomaly alert or triage notification to all active proctor clients."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket client: {e}")
                self.disconnect(connection)


stream_manager = ProctorStreamManager()


# =========================================================================
# Schemas
# =========================================================================

class ProctorDecisionRequest(BaseModel):
    proctor_id: str = Field(..., description="ID of human proctor performing action")
    action: str = Field(
        ...,
        description="Action type: APPROVE_IDENTITY | ISSUE_WARNING | TERMINATE_SESSION | CLEAR_VIOLATION | DISMISS_ALERT"
    )
    notes: Optional[str] = Field(default=None, description="Proctor rationale / explanation")
    evidence_event_id: Optional[str] = Field(default=None, description="Specific violation ID if clearing/confirming")


class ProctorDecisionResponse(BaseModel):
    session_id: str
    proctor_id: str
    action_applied: str
    previous_status: str
    new_status: str
    warning_count: int
    cumulative_risk_score: float
    timestamp: str
    message: str


# =========================================================================
# Endpoints
# =========================================================================

@router.get("/sessions")
def list_active_sessions(
    min_risk: Optional[float] = Query(default=0.0, description="Minimum cumulative risk score filter"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status (ACTIVE, TERMINATED, PENDING_REVIEW)")
):
    """
    Lists active exam sessions with real-time risk indicators, warning counts, and HITL flags.
    Allows filtering by risk score threshold or session status.
    """
    results = []
    for sess_id, sess in ACTIVE_SESSIONS.items():
        score = sess.get("cumulative_risk_score", 0.0)
        curr_status = sess.get("status", "ACTIVE")
        if score < min_risk:
            continue
        if status_filter and curr_status.upper() != status_filter.upper():
            continue

        results.append({
            "session_id": sess_id,
            "candidate_id": sess.get("candidate_id"),
            "exam_id": sess.get("exam_id"),
            "started_at": sess.get("started_at"),
            "status": curr_status,
            "cumulative_risk_score": score,
            "warning_count": sess.get("warning_count", 0),
            "latest_decision": sess.get("latest_decision", "CONTINUE"),
            "requires_human_triage": sess.get("latest_decision") in ["ESCALATE_HUMAN", "TERMINATE"]
        })

    # Sort descending by cumulative risk score
    results.sort(key=lambda x: x["cumulative_risk_score"], reverse=True)
    return {
        "total_active_sessions": len(results),
        "sessions": results
    }


@router.get("/sessions/{session_id}/timeline")
def get_session_timeline(session_id: str):
    """
    Retrieves the chronological audit trail and evidence events for an exam session.
    Queries the checkpoint state engine to provide an immutable forensic log.
    """
    saved_state = proctoring_graph.checkpointer.get(session_id)
    events = saved_state.get("evidence_events", []) if saved_state else []

    sorted_timeline = timeline_builder.build_timeline(events)

    active_sess = ACTIVE_SESSIONS.get(session_id, {})
    candidate_id = active_sess.get("candidate_id", saved_state.get("candidate_id", "UNKNOWN") if saved_state else "UNKNOWN")
    risk_score = active_sess.get("cumulative_risk_score", saved_state.get("cumulative_risk_score", 0.0) if saved_state else 0.0)
    warn_count = active_sess.get("warning_count", saved_state.get("warning_count", 0) if saved_state else 0)
    decision = active_sess.get("latest_decision", saved_state.get("orchestrator_decision", "CONTINUE") if saved_state else "CONTINUE")

    summary = timeline_builder.generate_session_summary(
        session_id=session_id,
        candidate_id=candidate_id,
        cumulative_risk=risk_score,
        warning_count=warn_count,
        decision=decision,
        events=sorted_timeline
    )

    return {
        "session_summary": summary,
        "timeline": sorted_timeline
    }


@router.post("/sessions/{session_id}/decision", response_model=ProctorDecisionResponse)
async def submit_proctor_decision(session_id: str, payload: ProctorDecisionRequest):
    """
    Submits a manual Human-in-the-Loop proctor decision.
    Supported actions:
    - APPROVE_IDENTITY: Resolves a PENDING_HUMAN_REVIEW identity challenge
    - ISSUE_WARNING: Issues an official verbal/visual warning (+1 warning count)
    - TERMINATE_SESSION: Forcibly halts candidate exam session due to verified malpractice
    - CLEAR_VIOLATION: Lowers risk score by dismissing a false positive
    - DISMISS_ALERT: Acknowledges an alert without action
    """
    if session_id not in ACTIVE_SESSIONS:
        # Create or check if exists in checkpointer
        saved_state = proctoring_graph.checkpointer.get(session_id)
        if not saved_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found."
            )
        ACTIVE_SESSIONS[session_id] = {
            "session_id": session_id,
            "candidate_id": saved_state.get("candidate_id", "UNKNOWN"),
            "exam_id": "DEFAULT_EXAM",
            "started_at": saved_state.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "status": "ACTIVE",
            "cumulative_risk_score": saved_state.get("cumulative_risk_score", 0.0),
            "warning_count": saved_state.get("warning_count", 0),
            "latest_decision": saved_state.get("orchestrator_decision", "CONTINUE")
        }

    session = ACTIVE_SESSIONS[session_id]
    prev_status = session.get("status", "ACTIVE")
    action = payload.action.upper()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Process action
    if action == "TERMINATE_SESSION":
        session["status"] = "TERMINATED"
        session["latest_decision"] = "TERMINATE"
        msg = f"Session terminated by proctor {payload.proctor_id}. Reason: {payload.notes or 'Proctor directive.'}"
    elif action == "ISSUE_WARNING":
        session["warning_count"] = session.get("warning_count", 0) + 1
        session["latest_decision"] = "WARN"
        msg = f"Official warning issued by proctor {payload.proctor_id}. Total warnings: {session['warning_count']}."
    elif action == "APPROVE_IDENTITY":
        session["status"] = "ACTIVE"
        session["latest_decision"] = "CONTINUE"
        msg = f"Identity challenge approved by proctor {payload.proctor_id}."
    elif action == "CLEAR_VIOLATION":
        # Deduct 25 points from cumulative risk score
        session["cumulative_risk_score"] = max(0.0, session.get("cumulative_risk_score", 0.0) - 25.0)
        msg = f"Violation cleared by proctor {payload.proctor_id}. Risk score reduced."
    elif action == "DISMISS_ALERT":
        session["latest_decision"] = "CONTINUE"
        msg = f"Alert dismissed by proctor {payload.proctor_id}."
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown proctor action '{payload.action}'. Valid options: APPROVE_IDENTITY, ISSUE_WARNING, TERMINATE_SESSION, CLEAR_VIOLATION, DISMISS_ALERT."
        )

    # Append human proctor decision event to checkpointer immutable log
    saved_state = proctoring_graph.checkpointer.get(session_id) or {}
    evidence_events = saved_state.get("evidence_events", [])
    proctor_event = {
        "event_id": f"proctor_{int(datetime.now().timestamp() * 1000)}",
        "session_id": session_id,
        "candidate_id": session.get("candidate_id", "UNKNOWN"),
        "timestamp": now_iso,
        "anomaly_type": f"PROCTOR_ACTION_{action}",
        "severity": AnomalySeverity.LOW.value if action in ["APPROVE_IDENTITY", "CLEAR_VIOLATION"] else AnomalySeverity.CRITICAL.value,
        "risk_weight": 0.0,
        "confidence": 1.0,
        "source": "PROCTOR_HITL_INTERVENTION",
        "summary": msg,
        "proctor_review_status": "CONFIRMED" if action in ["ISSUE_WARNING", "TERMINATE_SESSION"] else "DISMISSED"
    }
    evidence_events.append(proctor_event)
    saved_state["evidence_events"] = evidence_events
    saved_state["cumulative_risk_score"] = session["cumulative_risk_score"]
    saved_state["warning_count"] = session["warning_count"]
    saved_state["orchestrator_decision"] = session["latest_decision"]
    proctoring_graph.checkpointer.put(session_id, saved_state)

    # Broadcast event to WebSocket subscribers
    alert_payload = {
        "type": "PROCTOR_DECISION_APPLIED",
        "session_id": session_id,
        "action": action,
        "proctor_id": payload.proctor_id,
        "timestamp": now_iso,
        "message": msg
    }
    await stream_manager.broadcast_alert(alert_payload)

    return ProctorDecisionResponse(
        session_id=session_id,
        proctor_id=payload.proctor_id,
        action_applied=action,
        previous_status=prev_status,
        new_status=session["status"],
        warning_count=session["warning_count"],
        cumulative_risk_score=session["cumulative_risk_score"],
        timestamp=now_iso,
        message=msg
    )


# =========================================================================
# WebSocket Live Proctor Stream
# =========================================================================

@router.websocket("/stream")
async def proctor_live_stream(websocket: WebSocket):
    """
    Real-time WebSocket connection for live proctor dashboard.
    Receives continuous streaming alerts, candidate status changes, and anomaly events.
    """
    await stream_manager.connect(websocket)
    try:
        # Initial greeting packet
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_sessions_count": len(ACTIVE_SESSIONS)
        })

        while True:
            # Keep connection alive and respond to client pings
            data = await websocket.receive_text()
            if data.strip().upper() == "PING":
                await websocket.send_text("PONG")
            else:
                await websocket.send_json({"type": "ACK", "payload": data})
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        stream_manager.disconnect(websocket)
