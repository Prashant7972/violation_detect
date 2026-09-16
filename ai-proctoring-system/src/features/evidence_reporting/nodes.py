"""
Evidence Synthesis & Risk Scorer LangGraph Node
Aggregates policy breaches, accumulates risk score clamped at 100.0,
and synthesizes explainable evidence audit records.
"""

import logging
from typing import Dict, Any, List

from src.core.config import settings
from src.core.state import ProctorSessionState
from src.core.gemini_client import gemini_client
from src.features.evidence_reporting.schemas import EvidenceEvent
from src.features.vision_proctoring.schemas import AnomalySeverity

logger = logging.getLogger("evidence_synthesis_node")


def evidence_synthesis_node(state: ProctorSessionState) -> Dict[str, Any]:
    """
    LangGraph node for evidence synthesis and risk scoring.
    Acts as the 'Chief Proctor Evaluation Model', aggregating policy violations,
    computing the delta risk, updating cumulative risk (clamped at 100.0),
    and deriving orchestrator decisions (CONTINUE | WARN_CANDIDATE | ESCALATE_HUMAN | TERMINATE).
    """
    session_id = state.get("session_id", "UNKNOWN_SESSION")
    candidate_id = state.get("candidate_id", "UNKNOWN_CANDIDATE")
    timestamp = state.get("timestamp", "UNKNOWN_TIMESTAMP")
    
    # Use current step's newly evaluated violations for risk delta calculation
    current_step_violations = state.get("step_violations", state.get("policy_violations", []))
    all_accumulated_violations = state.get("policy_violations", [])
    current_cumulative = state.get("cumulative_risk_score", 0.0)
    warning_count = state.get("warning_count", 0)

    # 1. Compute Base Penalty Points Delta from Current Step Violations
    risk_delta = 0.0
    highest_severity = AnomalySeverity.LOW
    has_critical = False

    for v in current_step_violations:
        pts = float(v.get("penalty_points", 0.0))
        risk_delta += pts
        sev_str = v.get("severity", "LOW")
        if sev_str == AnomalySeverity.CRITICAL.value:
            highest_severity = AnomalySeverity.CRITICAL
            has_critical = True
        elif sev_str == AnomalySeverity.HIGH.value and highest_severity != AnomalySeverity.CRITICAL:
            highest_severity = AnomalySeverity.HIGH
        elif sev_str == AnomalySeverity.MEDIUM.value and highest_severity not in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
            highest_severity = AnomalySeverity.MEDIUM

    # 2. Invoke Gemini for Reasoning & Synthesis if Current Violations Exist
    rationale = "Candidate examination environment within acceptable operating parameters."
    if current_step_violations:
        prompt = (
            f"Chief Proctor Evaluation for session {session_id}.\n"
            f"Candidate ID: {candidate_id}\n"
            f"Active Policy Violations: {current_step_violations}\n"
            f"Current Cumulative Risk: {current_cumulative}\n"
            f"Synthesize this into an explainable rationale and recommended action."
        )
        gemini_result = gemini_client.generate_risk_synthesis(prompt)
        rationale = gemini_result.get(
            "rationale",
            f"Accumulated {len(current_step_violations)} policy breaches including {current_step_violations[0].get('violation_id')}."
        )

    # 3. Update Cumulative Risk Score (Strictly clamped between 0.0 and 100.0)
    new_cumulative = round(min(settings.MAX_CUMULATIVE_RISK_SCORE, current_cumulative + risk_delta), 1)

    # 4. Determine Orchestrator Decision
    # Automated decisions are NEVER final for candidate disqualification —
    # high/critical severity triggers ESCALATE_HUMAN or TERMINATE pending proctor confirmation.
    decision = "CONTINUE"
    new_warnings = warning_count

    if new_cumulative >= settings.TERMINATION_THRESHOLD:
        decision = "TERMINATE"
    elif has_critical or new_cumulative >= settings.ESCALATE_HUMAN_THRESHOLD:
        decision = "ESCALATE_HUMAN"
    elif new_cumulative >= settings.WARNING_RISK_THRESHOLD:
        decision = "WARN_CANDIDATE"
        new_warnings += 1

    # 5. Build New Structured Evidence Events
    new_events: List[Dict[str, Any]] = []
    if current_step_violations:
        for v in current_step_violations:
            event = EvidenceEvent(
                session_id=session_id,
                candidate_id=candidate_id,
                timestamp=timestamp,
                event_source=v.get("source_detection", "PRIMARY_WEBCAM"),
                severity=AnomalySeverity(v.get("severity", "MEDIUM")),
                confidence=float(v.get("confidence", 0.90)),
                frame_reference=f"s3://{settings.S3_BUCKET_NAME}/{session_id}/frames/{timestamp}.jpg",
                detections=v.get("metadata", {}),
                policy_rule_triggered=v.get("violation_id", "POLICY_BREACH"),
                reasoning=rationale,
                system_action="FLAGGED_FOR_HUMAN_TRIAGE" if decision in ["ESCALATE_HUMAN", "TERMINATE"] else "AUTO_RECORDED",
                proctor_review_status="PENDING_VERIFICATION"
            )
            new_events.append(event.model_dump())

    return {
        "risk_score_delta": risk_delta,
        "cumulative_risk_score": new_cumulative,
        "warning_count": new_warnings,
        "orchestrator_decision": decision,
        "evidence_events": new_events
    }
