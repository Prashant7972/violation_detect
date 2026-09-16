"""
Schemas and Data Contracts for Audio Intelligence Feature
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.features.vision_proctoring.schemas import AnomalySeverity


class AudioEventType(str, Enum):
    SILENCE = "SILENCE"
    NORMAL_BACKGROUND = "NORMAL_BACKGROUND"
    WHISPERING = "WHISPERING"
    MULTIPLE_VOICES = "MULTIPLE_VOICES"
    READING_ALOUD_OR_DICTATION = "READING_ALOUD_OR_DICTATION"
    MECHANICAL_KEYBOARD_OR_CLICKING = "MECHANICAL_KEYBOARD_OR_CLICKING"
    UNKNOWN = "UNKNOWN"


class AudioAnomalyItem(BaseModel):
    """Acoustic or speech anomaly detected in the microphone stream."""
    type: str = Field(..., description="Anomaly classification code")
    severity: AnomalySeverity
    timestamp: str
    details: str
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AudioAnalysisResult(BaseModel):
    """Structured response contract for audio intelligence evaluation."""
    transcript: Optional[str] = Field(default=None, description="Transcribed spoken words from candidate microphone")
    primary_event: AudioEventType = Field(
        default=AudioEventType.NORMAL_BACKGROUND,
        description="Dominant acoustic classification"
    )
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    contains_speech: bool = Field(default=False, description="True if intelligible speech was detected")
    anomalies: List[AudioAnomalyItem] = Field(default_factory=list)
