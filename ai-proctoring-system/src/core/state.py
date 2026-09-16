"""
Shared LangGraph Session State Definition for AI Remote Proctoring System
"""

import operator
from typing import Annotated, List, Dict, Any, Optional, TypedDict


class ProctorSessionState(TypedDict):
    """
    Complete state dictionary managed by the LangGraph supervisor workflow.
    Fields marked with Annotated[..., operator.add] accumulate across steps.
    """
    
    # 1. Session Context
    session_id: str
    candidate_id: str
    timestamp: str
    
    # 2. Raw Media Payloads
    primary_frame_bytes: Optional[bytes]
    secondary_frame_bytes: Optional[bytes]
    audio_chunk_bytes: Optional[bytes]
    audio_transcript: Optional[str]
    
    # 3. Vision Analysis Signals
    face_count: int
    face_matched: bool
    detected_objects: Annotated[List[Dict[str, Any]], operator.add]
    visual_anomalies: Annotated[List[Dict[str, Any]], operator.add]
    
    # 4. Audio Intelligence Signals
    audio_anomalies: Annotated[List[Dict[str, Any]], operator.add]
    
    # 5. Policy Violations
    policy_violations: Annotated[List[Dict[str, Any]], operator.add]
    
    # 6. Scoring & Audit Controls
    risk_score_delta: float
    cumulative_risk_score: float
    warning_count: int
    evidence_events: Annotated[List[Dict[str, Any]], operator.add]
    
    # 7. Orchestrator Decision: CONTINUE | WARN_CANDIDATE | ESCALATE_HUMAN | TERMINATE
    orchestrator_decision: str
