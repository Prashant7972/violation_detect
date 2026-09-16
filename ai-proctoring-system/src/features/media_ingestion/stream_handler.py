"""
Stream Handler for Continuous Multi-Angle Media Ingestion
Manages WebRTC / RTSP / HTTP dual-stream ingestion for primary webcam and candidate mobile secondary camera.
"""

import base64
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Optional, Deque, Tuple, List, Any

from src.features.media_ingestion.schemas import (
    CameraSource,
    FrameIngestPayload,
    AudioChunkPayload,
    SynchronizedMediaSample
)

logger = logging.getLogger("stream_handler")


class SessionMediaBuffer:
    """Ephemeral ring buffer for a single proctoring session."""
    
    def __init__(self, max_frames: int = 60, max_audio: int = 60):
        self.primary_frames: Deque[FrameIngestPayload] = deque(maxlen=max_frames)
        self.secondary_frames: Deque[FrameIngestPayload] = deque(maxlen=max_frames)
        self.audio_chunks: Deque[AudioChunkPayload] = deque(maxlen=max_audio)

    def clear(self):
        self.primary_frames.clear()
        self.secondary_frames.clear()
        self.audio_chunks.clear()


class StreamHandler:
    """
    Coordinates multi-angle continuous ingestion across active exam sessions.
    Maintains zero-egress ephemeral storage compliance by bounding in-memory buffer lifespans.
    """

    def __init__(self, max_buffer_per_session: int = 60):
        self._buffers: Dict[str, SessionMediaBuffer] = {}
        self.max_buffer_per_session = max_buffer_per_session

    def _get_or_create_buffer(self, session_id: str) -> SessionMediaBuffer:
        if session_id not in self._buffers:
            self._buffers[session_id] = SessionMediaBuffer(
                max_frames=self.max_buffer_per_session,
                max_audio=self.max_buffer_per_session
            )
        return self._buffers[session_id]

    @staticmethod
    def _ensure_bytes(payload: FrameIngestPayload) -> Optional[bytes]:
        """Resolves frame bytes from either direct bytes or base64 data string."""
        if payload.frame_bytes:
            return payload.frame_bytes
        if payload.frame_b64:
            try:
                b64 = payload.frame_b64
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                return base64.b64decode(b64)
            except Exception as e:
                logger.error(f"Failed to decode base64 frame: {e}")
        return None

    def ingest_frame(self, payload: FrameIngestPayload) -> bool:
        """
        Ingests a frame from either primary webcam or secondary mobile camera.
        Stores in session ring buffer.
        """
        raw_bytes = self._ensure_bytes(payload)
        if not raw_bytes:
            logger.warning(f"Rejected empty frame from {payload.source} in session {payload.session_id}")
            return False

        payload.frame_bytes = raw_bytes
        buf = self._get_or_create_buffer(payload.session_id)

        if payload.source == CameraSource.PRIMARY_WEBCAM:
            buf.primary_frames.append(payload)
        elif payload.source == CameraSource.SECONDARY_MOBILE:
            buf.secondary_frames.append(payload)
        else:
            logger.warning(f"Unknown camera source: {payload.source}")
            return False

        return True

    def ingest_audio(self, payload: AudioChunkPayload) -> bool:
        """Ingests an audio chunk into the session buffer."""
        if not payload.audio_bytes and payload.audio_b64:
            try:
                b64 = payload.audio_b64
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                payload.audio_bytes = base64.b64decode(b64)
            except Exception as e:
                logger.error(f"Failed to decode audio base64: {e}")
                return False

        if not payload.audio_bytes:
            return False

        buf = self._get_or_create_buffer(payload.session_id)
        buf.audio_chunks.append(payload)
        return True

    def get_latest_synchronized_sample(
        self,
        session_id: str,
        candidate_id: str,
        max_skew_ms: float = 1000.0
    ) -> Optional[SynchronizedMediaSample]:
        """
        Pulls the latest primary frame and pairs it with the closest timestamped
        secondary mobile frame and audio chunk within the allowed time skew.
        """
        buf = self._buffers.get(session_id)
        if not buf or len(buf.primary_frames) == 0:
            return None

        primary = buf.primary_frames[-1]
        p_bytes = primary.frame_bytes
        s_bytes = None
        a_bytes = None
        skew_ms = 0.0

        # Try parsing primary timestamp
        try:
            p_time = datetime.fromisoformat(primary.timestamp.replace("Z", "+00:00"))
        except Exception:
            p_time = datetime.now(timezone.utc)

        # Pair closest secondary frame
        if len(buf.secondary_frames) > 0:
            best_sec = None
            min_diff = float("inf")
            for sec in reversed(buf.secondary_frames):
                try:
                    s_time = datetime.fromisoformat(sec.timestamp.replace("Z", "+00:00"))
                    diff = abs((p_time - s_time).total_seconds() * 1000.0)
                    if diff < min_diff:
                        min_diff = diff
                        best_sec = sec
                    if diff <= max_skew_ms:
                        break
                except Exception:
                    continue

            if best_sec and min_diff <= max_skew_ms:
                s_bytes = best_sec.frame_bytes
                skew_ms = min_diff

        # Pair latest audio chunk
        if len(buf.audio_chunks) > 0:
            a_bytes = buf.audio_chunks[-1].audio_bytes

        return SynchronizedMediaSample(
            session_id=session_id,
            candidate_id=candidate_id,
            timestamp=primary.timestamp,
            primary_frame_bytes=p_bytes,
            secondary_frame_bytes=s_bytes,
            audio_chunk_bytes=a_bytes,
            has_primary=p_bytes is not None,
            has_secondary=s_bytes is not None,
            has_audio=a_bytes is not None,
            time_delta_ms=skew_ms
        )

    def flush_session_buffer(self, session_id: str) -> bool:
        """
        Compliance control: Immediately flushes ephemeral frame and audio buffers
        once downstream graph processing completes, unless retained as violation evidence.
        """
        if session_id in self._buffers:
            self._buffers[session_id].clear()
            del self._buffers[session_id]
            logger.info(f"Flushed ephemeral media buffer for session {session_id}")
            return True
        return False

    def get_buffer_stats(self, session_id: str) -> Dict[str, int]:
        """Returns the current buffer depth for monitoring and health metrics."""
        buf = self._buffers.get(session_id)
        if not buf:
            return {"primary_frames": 0, "secondary_frames": 0, "audio_chunks": 0}
        return {
            "primary_frames": len(buf.primary_frames),
            "secondary_frames": len(buf.secondary_frames),
            "audio_chunks": len(buf.audio_chunks)
        }


# Global stream handler instance
stream_handler = StreamHandler()
