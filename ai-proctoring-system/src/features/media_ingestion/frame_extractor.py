"""
Frame Extractor & Scheduler Module
Handles periodic sampling of frames from multi-angle stream buffers
and formats them for consumption by the LangGraph supervisor.
"""

import time
import cv2
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator, Tuple

from src.core.config import settings
from src.core.state import ProctorSessionState
from src.features.media_ingestion.schemas import (
    CameraSource,
    FrameIngestPayload,
    SynchronizedMediaSample
)
from src.features.media_ingestion.stream_handler import stream_handler, StreamHandler

logger = logging.getLogger("frame_extractor")


class FrameExtractor:
    """
    Samples timestamped frames and audio chunks from active stream buffers
    and builds populated ProctorSessionState dictionaries.
    """

    def __init__(self, handler: Optional[StreamHandler] = None, interval_seconds: Optional[float] = None):
        self.handler = handler or stream_handler
        self.interval_seconds = interval_seconds or settings.FRAME_SAMPLE_INTERVAL_SECONDS
        self._last_sample_timestamps: Dict[str, float] = {}

    def is_due_for_sampling(self, session_id: str) -> bool:
        """Determines if the session has reached its next scheduled sampling interval."""
        now = time.time()
        last = self._last_sample_timestamps.get(session_id, 0.0)
        if now - last >= self.interval_seconds:
            self._last_sample_timestamps[session_id] = now
            return True
        return False

    def extract_state_payload(
        self,
        session_id: str,
        candidate_id: str,
        force: bool = False
    ) -> Optional[ProctorSessionState]:
        """
        Pulls a synchronized multi-angle frame pair and audio chunk from the buffer,
        constructing an initial ProctorSessionState dict for graph execution.
        """
        if not force and not self.is_due_for_sampling(session_id):
            return None

        sample: Optional[SynchronizedMediaSample] = self.handler.get_latest_synchronized_sample(
            session_id=session_id,
            candidate_id=candidate_id
        )

        if not sample or not sample.has_primary:
            return None

        current_time = sample.timestamp or datetime.now(timezone.utc).isoformat()

        # Build initial ProctorSessionState for LangGraph invocation
        state: ProctorSessionState = {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "timestamp": current_time,
            "primary_frame_bytes": sample.primary_frame_bytes,
            "secondary_frame_bytes": sample.secondary_frame_bytes,
            "audio_chunk_bytes": sample.audio_chunk_bytes,
            "audio_transcript": None,
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
        return state

    @staticmethod
    def encode_numpy_frame(frame: np.ndarray, format: str = ".jpg") -> bytes:
        """Encodes an OpenCV BGR numpy frame to compressed JPEG bytes."""
        success, buffer = cv2.imencode(format, frame)
        if not success:
            raise ValueError("Could not encode frame to JPEG format")
        return buffer.tobytes()

    @classmethod
    def simulate_video_stream(
        cls,
        video_path: str,
        session_id: str,
        candidate_id: str,
        source: CameraSource = CameraSource.PRIMARY_WEBCAM,
        sample_fps: float = 1.0
    ) -> Generator[FrameIngestPayload, None, None]:
        """
        Utility for testing: Reads an MP4/video file and yields timestamped FrameIngestPayload items.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open video file at {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = int(round(fps / sample_fps))
        frame_idx = 0
        seq_num = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    encoded_bytes = cls.encode_numpy_frame(frame)
                    now_iso = datetime.now(timezone.utc).isoformat()
                    yield FrameIngestPayload(
                        session_id=session_id,
                        candidate_id=candidate_id,
                        source=source,
                        timestamp=now_iso,
                        sequence_number=seq_num,
                        frame_bytes=encoded_bytes
                    )
                    seq_num += 1

                frame_idx += 1
        finally:
            cap.release()


# Global frame extractor instance
frame_extractor = FrameExtractor()
