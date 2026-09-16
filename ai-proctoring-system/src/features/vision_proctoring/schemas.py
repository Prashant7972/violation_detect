"""
Schemas and Data Contracts for Vision Proctoring Feature
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GazeAssessment(str, Enum):
    FORWARD = "FORWARD"
    LOOKING_AWAY = "LOOKING_AWAY"
    LOOKING_DOWN = "LOOKING_DOWN"
    SUSPICIOUS = "SUSPICIOUS"


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DetectedObjectItem(BaseModel):
    """An unauthorized or flagged object detected in the video stream."""
    name: str = Field(..., description="Object label, e.g. smartphone, secondary_screen, earbud, book")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence rating between 0.0 and 1.0")
    bounding_box: Optional[List[int]] = Field(
        default=None,
        description="Bounding coordinates [ymin, xmin, ymax, xmax] normalized 0-1000 or absolute pixels"
    )


class VisualAnomalyItem(BaseModel):
    """A visual anomaly event derived from face count, gaze, or prohibited objects."""
    type: str = Field(..., description="Anomaly type, e.g. NO_FACE_DETECTED, MULTIPLE_FACES_DETECTED, SUSPICIOUS_GAZE")
    severity: AnomalySeverity
    timestamp: str
    details: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VisionAnalysisResponse(BaseModel):
    """Structured response contract expected from the Gemini multimodal vision model."""
    face_count: int = Field(default=1, ge=0, description="Number of human faces visible in the frame")
    face_detected: bool = Field(default=True, description="True if at least one face is clearly present")
    unauthorized_objects: List[DetectedObjectItem] = Field(
        default_factory=list,
        description="List of detected prohibited objects (phones, tablets, secondary displays, notes)"
    )
    gaze_assessment: GazeAssessment = Field(
        default=GazeAssessment.FORWARD,
        description="Assessment of candidate eye gaze and head orientation"
    )
    anomaly_summary: str = Field(
        default="Candidate facing display normally.",
        description="Concise description of visual observations"
    )
