"""
Schemas and Data Contracts for Policy Rules and RAG Evaluator
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.features.vision_proctoring.schemas import AnomalySeverity


class PolicyViolation(BaseModel):
    """An official policy breach record derived from cross-referencing anomalies against rules."""
    violation_id: str = Field(..., description="Unique violation code e.g. PROHIBITED_DEVICE")
    rule_category: str = Field(..., description="HARDWARE | IDENTITY | GAZE | ACOUSTIC")
    severity: AnomalySeverity
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    details: str
    timestamp: str
    source_detection: str = Field(..., description="PRIMARY_WEBCAM | SECONDARY_MOBILE | AUDIO")
    penalty_points: float = Field(default=0.0, ge=0.0, description="Risk score addition for this violation")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    """Aggregated evaluation of all active policy breaches for the current step."""
    violations: List[PolicyViolation] = Field(default_factory=list)
    total_violations_count: int = 0
    max_severity: AnomalySeverity = AnomalySeverity.LOW
    total_penalty_points: float = 0.0
