"""
Schemas and Data Contracts for Evidence Reporting & Timeline Synthesis
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.features.vision_proctoring.schemas import AnomalySeverity


class EvidenceEvent(BaseModel):
    """
    Immutable audit record for an anomaly or policy breach during the exam.
    Matches the schema defined in the project specification.
    """
    session_id: str
    candidate_id: str
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    event_source: str = Field(default="PRIMARY_WEBCAM", description="PRIMARY_WEBCAM | SECONDARY_MOBILE | AUDIO")
    severity: AnomalySeverity
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    frame_reference: Optional[str] = Field(
        default=None,
        description="S3 URI or storage path to evidence snapshot e.g. s3://proctor-media/sess_123/frames/frame_01.jpg"
    )
    detections: Dict[str, Any] = Field(default_factory=dict)
    policy_rule_triggered: str = Field(..., description="Policy rule or anomaly code")
    reasoning: str = Field(..., description="Explainable justification of why this event was flagged")
    system_action: str = Field(
        default="FLAGGED_FOR_HUMAN_TRIAGE",
        description="FLAGGED_FOR_HUMAN_TRIAGE | CANDIDATE_WARNED | AUTO_RECORDED"
    )
    proctor_review_status: str = Field(
        default="PENDING_VERIFICATION",
        description="PENDING_VERIFICATION | CONFIRMED_VIOLATION | DISMISSED_FALSE_POSITIVE"
    )


class EvidenceSynthesisResponse(BaseModel):
    """Output from the evidence synthesis & chief proctor evaluation node."""
    risk_score_delta: float = Field(default=0.0, ge=0.0)
    cumulative_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    orchestrator_decision: str = Field(
        default="CONTINUE",
        description="CONTINUE | WARN_CANDIDATE | ESCALATE_HUMAN | TERMINATE"
    )
    rationale: str = Field(default="Normal candidate behavior.", description="Explainable reasoning summary")
    severity_level: AnomalySeverity = AnomalySeverity.LOW
    evidence_events: List[EvidenceEvent] = Field(default_factory=list)
