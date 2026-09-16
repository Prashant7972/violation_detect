"""
Unit Tests for Media Ingestion Feature (Step 2)
"""

import sys
import os
import cv2
import time
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta

# Add src to sys.path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.features.media_ingestion.schemas import (
    CameraSource,
    FrameIngestPayload,
    AudioChunkPayload,
    SynchronizedMediaSample
)
from src.features.media_ingestion.stream_handler import StreamHandler
from src.features.media_ingestion.frame_extractor import FrameExtractor


def create_dummy_jpeg(color=(100, 150, 200), width=320, height=240) -> bytes:
    """Helper to create dummy JPEG bytes."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def test_primary_and_secondary_stream_ingest():
    """Verifies that primary and secondary camera frames are ingested into isolated buffers."""
    handler = StreamHandler(max_buffer_per_session=10)
    sess_id = "sess_test_001"
    cand_id = "cand_test_001"
    now_iso = datetime.now(timezone.utc).isoformat()

    p_frame = FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.PRIMARY_WEBCAM,
        timestamp=now_iso,
        sequence_number=1,
        frame_bytes=create_dummy_jpeg((120, 180, 240))
    )

    s_frame = FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.SECONDARY_MOBILE,
        timestamp=now_iso,
        sequence_number=1,
        frame_bytes=create_dummy_jpeg((50, 80, 120))
    )

    assert handler.ingest_frame(p_frame) is True
    assert handler.ingest_frame(s_frame) is True

    stats = handler.get_buffer_stats(sess_id)
    assert stats["primary_frames"] == 1
    assert stats["secondary_frames"] == 1
    assert stats["audio_chunks"] == 0


def test_synchronized_multi_angle_sampling():
    """Verifies timestamp alignment when pairing primary and secondary mobile frames."""
    handler = StreamHandler()
    sess_id = "sess_test_002"
    cand_id = "cand_test_002"

    t0 = datetime.now(timezone.utc)
    t_primary = t0.isoformat()
    t_secondary = (t0 + timedelta(milliseconds=80)).isoformat()  # 80ms skew

    handler.ingest_frame(FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.PRIMARY_WEBCAM,
        timestamp=t_primary,
        sequence_number=1,
        frame_bytes=create_dummy_jpeg((200, 200, 200))
    ))

    handler.ingest_frame(FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.SECONDARY_MOBILE,
        timestamp=t_secondary,
        sequence_number=1,
        frame_bytes=create_dummy_jpeg((100, 100, 100))
    ))

    # Add audio chunk
    handler.ingest_audio(AudioChunkPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        timestamp=t_primary,
        duration_ms=1000,
        sample_rate=16000,
        audio_bytes=b"dummy_pcm_audio_bytes_data"
    ))

    sample = handler.get_latest_synchronized_sample(sess_id, cand_id, max_skew_ms=500.0)
    assert sample is not None
    assert sample.has_primary is True
    assert sample.has_secondary is True
    assert sample.has_audio is True
    assert 0.0 < sample.time_delta_ms <= 100.0  # Approx 80ms skew detected


def test_time_skew_rejection():
    """Verifies that a stale secondary frame (> max_skew_ms) is not paired."""
    handler = StreamHandler()
    sess_id = "sess_test_003"
    cand_id = "cand_test_003"

    t0 = datetime.now(timezone.utc)
    t_primary = t0.isoformat()
    t_stale_secondary = (t0 - timedelta(seconds=5)).isoformat()  # 5000ms stale

    handler.ingest_frame(FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.PRIMARY_WEBCAM,
        timestamp=t_primary,
        sequence_number=5,
        frame_bytes=create_dummy_jpeg()
    ))

    handler.ingest_frame(FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.SECONDARY_MOBILE,
        timestamp=t_stale_secondary,
        sequence_number=1,
        frame_bytes=create_dummy_jpeg()
    ))

    sample = handler.get_latest_synchronized_sample(sess_id, cand_id, max_skew_ms=1000.0)
    assert sample is not None
    assert sample.has_primary is True
    assert sample.has_secondary is False  # Stale secondary rejected


def test_frame_extractor_state_payload():
    """Verifies that FrameExtractor constructs a compliant ProctorSessionState dictionary."""
    handler = StreamHandler()
    extractor = FrameExtractor(handler=handler, interval_seconds=0.1)
    sess_id = "sess_test_004"
    cand_id = "cand_test_004"

    handler.ingest_frame(FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.PRIMARY_WEBCAM,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sequence_number=1,
        frame_bytes=create_dummy_jpeg()
    ))

    state = extractor.extract_state_payload(sess_id, cand_id, force=True)
    assert state is not None
    assert state["session_id"] == sess_id
    assert state["candidate_id"] == cand_id
    assert state["primary_frame_bytes"] is not None
    assert state["detected_objects"] == []
    assert state["orchestrator_decision"] == "CONTINUE"


def test_ephemeral_buffer_flushing():
    """Verifies compliance control: buffers are completely wiped on flush."""
    handler = StreamHandler()
    sess_id = "sess_flush_test"
    cand_id = "cand_flush_test"

    handler.ingest_frame(FrameIngestPayload(
        session_id=sess_id,
        candidate_id=cand_id,
        source=CameraSource.PRIMARY_WEBCAM,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sequence_number=1,
        frame_bytes=create_dummy_jpeg()
    ))

    stats_before = handler.get_buffer_stats(sess_id)
    assert stats_before["primary_frames"] == 1

    assert handler.flush_session_buffer(sess_id) is True
    stats_after = handler.get_buffer_stats(sess_id)
    assert stats_after["primary_frames"] == 0
