"""
Unit Tests for Audio Intelligence Feature (Step 4)
"""

import sys
import os
import pytest
import numpy as np

# Add src to sys.path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.state import ProctorSessionState
from src.features.audio_intelligence.schemas import AudioEventType
from src.features.audio_intelligence.transcriber import audio_transcriber
from src.features.audio_intelligence.nodes import audio_intelligence_node


def create_synthetic_pcm_audio(duration_ms=1000, sample_rate=16000, amplitude=0.0) -> bytes:
    """Helper to generate synthetic PCM 16-bit mono audio bytes."""
    num_samples = int((duration_ms / 1000.0) * sample_rate)
    if amplitude == 0.0:
        samples = np.zeros(num_samples, dtype=np.int16)
    else:
        # Generate mild sinusoidal tone with specified amplitude
        t = np.linspace(0, duration_ms / 1000.0, num_samples, endpoint=False)
        waveform = amplitude * np.sin(2 * np.pi * 440 * t)
        samples = np.clip(waveform, -32768, 32767).astype(np.int16)
    return samples.tobytes()


def build_base_audio_state(audio_bytes=None, transcript=None) -> ProctorSessionState:
    """Helper to construct baseline ProctorSessionState for audio evaluation."""
    return {
        "session_id": "sess_audio_001",
        "candidate_id": "cand_audio_001",
        "timestamp": "2026-09-15T10:05:00Z",
        "primary_frame_bytes": None,
        "secondary_frame_bytes": None,
        "audio_chunk_bytes": audio_bytes,
        "audio_transcript": transcript,
        "face_count": 1,
        "face_matched": True,
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


def test_audio_node_silence_no_anomalies():
    """Verifies that ambient room silence produces zero audio anomalies."""
    silent_pcm = create_synthetic_pcm_audio(amplitude=0.0)
    state = build_base_audio_state(audio_bytes=silent_pcm)

    result = audio_intelligence_node(state)
    assert len(result["audio_anomalies"]) == 0


def test_audio_node_whispering_detected():
    """Verifies that low-level vocal energy in the whisper range triggers WHISPERING_DETECTED."""
    # Whisper amplitude range (RMS around 300)
    whisper_pcm = create_synthetic_pcm_audio(amplitude=450.0)
    state = build_base_audio_state(audio_bytes=whisper_pcm)

    result = audio_intelligence_node(state)
    assert len(result["audio_anomalies"]) >= 1
    types = [a["type"] for a in result["audio_anomalies"]]
    assert "WHISPERING_DETECTED" in types
    whisper_anomaly = next(a for a in result["audio_anomalies"] if a["type"] == "WHISPERING_DETECTED")
    assert whisper_anomaly["severity"] == "MEDIUM"


def test_audio_node_dictation_detected():
    """Verifies that spoken exam keywords trigger DICTATION_OR_COLLUSION_DETECTED anomaly."""
    transcript = "Can you tell me what is the answer to question five?"
    state = build_base_audio_state(transcript=transcript)

    result = audio_intelligence_node(state)
    assert len(result["audio_anomalies"]) == 1
    anomaly = result["audio_anomalies"][0]
    assert anomaly["type"] == "DICTATION_OR_COLLUSION_DETECTED"
    assert anomaly["severity"] == "HIGH"
    assert "what is the answer" in anomaly["details"].lower()


def test_audio_node_multiple_voices_dialogue():
    """Verifies that dialogue patterns trigger MULTIPLE_VOICES_DETECTED anomaly."""
    transcript = "Are you sure? yes, repeat option b"
    state = build_base_audio_state(transcript=transcript)

    result = audio_intelligence_node(state)
    assert len(result["audio_anomalies"]) >= 1
    types = [a["type"] for a in result["audio_anomalies"]]
    assert any(t in ["MULTIPLE_VOICES_DETECTED", "DICTATION_OR_COLLUSION_DETECTED"] for t in types)


def test_audio_node_missing_audio_handled_gracefully():
    """Verifies that passing None for audio does not crash the node and yields empty anomalies."""
    state = build_base_audio_state(audio_bytes=None, transcript=None)

    result = audio_intelligence_node(state)
    assert result["audio_transcript"] is None
    assert len(result["audio_anomalies"]) == 0
