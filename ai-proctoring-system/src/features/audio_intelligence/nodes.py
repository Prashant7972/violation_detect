"""
Audio Intelligence LangGraph Node
Performs acoustic screening, transcription audit, and anomalous vocal detection
(whispering, multiple voices, mechanical noise, dictation).
"""

import logging
from typing import Dict, Any, List

from src.core.state import ProctorSessionState
from src.features.audio_intelligence.transcriber import audio_transcriber
from src.features.audio_intelligence.schemas import AudioEventType, AudioAnomalyItem

logger = logging.getLogger("audio_intelligence_node")


def audio_intelligence_node(state: ProctorSessionState) -> Dict[str, Any]:
    """
    LangGraph node for real-time audio intelligence proctoring.
    Processes microphone chunk bytes and spoken transcript,
    identifying acoustic anomalies like whispering, dictation, and second voices.
    
    Returns partial state update:
        audio_transcript: Optional[str]
        audio_anomalies: List[Dict[str, Any]]
    """
    audio_bytes = state.get("audio_chunk_bytes")
    existing_transcript = state.get("audio_transcript")
    timestamp = state.get("timestamp", "UNKNOWN_TIMESTAMP")
    session_id = state.get("session_id", "UNKNOWN_SESSION")

    audio_anomalies: List[Dict[str, Any]] = []
    final_transcript = existing_transcript

    # 1. Acoustic Signal Screening (Energy / Whispering / Background)
    if audio_bytes:
        acoustic_res = audio_transcriber.analyze_audio_chunk(
            audio_bytes=audio_bytes,
            timestamp=timestamp,
            session_id=session_id
        )
        if acoustic_res.transcript:
            final_transcript = acoustic_res.transcript

        for a in acoustic_res.anomalies:
            audio_anomalies.append(a.model_dump())

    # 2. Transcript Semantic Screening (collusion keywords / dialogue)
    if final_transcript:
        event_type, transcript_anomaly = audio_transcriber.audit_transcript_content(
            transcript=final_transcript,
            timestamp=timestamp
        )
        if transcript_anomaly:
            audio_anomalies.append(transcript_anomaly.model_dump())

    return {
        "audio_transcript": final_transcript,
        "audio_anomalies": audio_anomalies
    }
