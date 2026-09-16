"""
Schemas and Data Contracts for Media Ingestion Feature
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CameraSource(str, Enum):
    PRIMARY_WEBCAM = "PRIMARY_WEBCAM"
    SECONDARY_MOBILE = "SECONDARY_MOBILE"


class FrameIngestPayload(BaseModel):
    """Payload for an individual video frame received from a camera stream."""
    session_id: str
    candidate_id: str
    source: CameraSource
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of capture")
    sequence_number: int = Field(..., ge=0, description="Monotonically increasing frame index")
    frame_bytes: Optional[bytes] = None
    frame_b64: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AudioChunkPayload(BaseModel):
    """Payload for an audio chunk received from the microphone stream."""
    session_id: str
    candidate_id: str
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of capture")
    duration_ms: int = Field(default=1000, description="Duration of audio chunk in milliseconds")
    sample_rate: int = Field(default=16000, description="Audio sampling rate in Hz")
    audio_bytes: Optional[bytes] = None
    audio_b64: Optional[str] = None


class SynchronizedMediaSample(BaseModel):
    """
    Coordinated multi-angle frame snapshot and audio chunk
    correlated by timestamp for downstream agent analysis.
    """
    session_id: str
    candidate_id: str
    timestamp: str
    primary_frame_bytes: Optional[bytes] = None
    secondary_frame_bytes: Optional[bytes] = None
    audio_chunk_bytes: Optional[bytes] = None
    has_primary: bool = False
    has_secondary: bool = False
    has_audio: bool = False
    time_delta_ms: float = Field(default=0.0, description="Time skew between primary and secondary frames in ms")
