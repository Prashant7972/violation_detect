import base64
import os
import json
import cv2
import shutil
import tempfile
import numpy as np
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.db.models import SessionModel, EventModel, EvidenceModel
from app.api import schemas
from app.ai.detector import detector, AIDetector
from app.ai.rule_engine import RuleEngine
from app.ai.video_processor import VideoProcessor

logger = logging.getLogger("app.api.endpoints")
router = APIRouter()

@router.post("/sessions", response_model=schemas.SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: schemas.CreateSessionRequest, db: Session = Depends(get_db)):
    """
    Creates a new monitoring session with status ACTIVE.
    """
    session_obj = SessionModel(
        user_id=payload.user_id,
        status="ACTIVE"
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    session_evidence_dir = os.path.join(settings.EVIDENCE_DIR, session_obj.id)
    os.makedirs(session_evidence_dir, exist_ok=True)

    logger.info(f"Created new session {session_obj.id} for user {session_obj.user_id}")
    return schemas.SessionResponse(
        session_id=session_obj.id,
        user_id=session_obj.user_id,
        status=session_obj.status,
        created_at=session_obj.created_at
    )

@router.post("/sessions/{session_id}/frames", response_model=schemas.ProcessFrameResponse)
def process_frame(session_id: str, payload: schemas.FramePayloadRequest, db: Session = Depends(get_db)):
    """
    Processes base64 frame payload synchronously.
    """
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if session_obj.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Session {session_id} is in status '{session_obj.status}'")

    try:
        raw_b64 = payload.frame_data
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]
        
        img_bytes = base64.b64decode(raw_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            raise ValueError("Decoded image is empty or invalid format")
    except Exception as e:
        logger.error(f"Frame decoding failure for session {session_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image frame payload: {str(e)}")

    detection_results = detector.detect(img_bgr)
    detections = detection_results.get("detections", [])
    triggered_rules = RuleEngine.evaluate(detections)

    events_generated: List[schemas.EventResponse] = []
    session_status = "CLEAN"

    if triggered_rules:
        session_status = "VIOLATION_DETECTED"
        session_evidence_dir = os.path.join(settings.EVIDENCE_DIR, session_id)
        os.makedirs(session_evidence_dir, exist_ok=True)

        for rule in triggered_rules:
            event_obj = EventModel(
                session_id=session_id,
                event_type=rule["event_type"],
                rule_triggered=rule["rule_triggered"],
                confidence=rule["confidence"]
            )
            db.add(event_obj)
            db.flush()

            flagged = rule.get("flagged_detections", [])
            annotated_frame = AIDetector.annotate_frame(img_bgr, flagged)
            
            filename = f"event_{event_obj.id}.jpg"
            file_path = os.path.join(session_evidence_dir, filename)
            rel_file_path = f"/evidence/{session_id}/{filename}"
            
            cv2.imwrite(file_path, annotated_frame)

            evidence_obj = EvidenceModel(
                event_id=event_obj.id,
                file_path=rel_file_path,
                bbox_json=json.dumps([d.get("bounding_box") for d in flagged if d.get("bounding_box")])
            )
            db.add(evidence_obj)
            db.commit()
            db.refresh(event_obj)

            events_generated.append(
                schemas.EventResponse(
                    event_id=event_obj.id,
                    event_type=event_obj.event_type,
                    rule_triggered=event_obj.rule_triggered,
                    confidence=event_obj.confidence,
                    evidence_path=rel_file_path,
                    created_at=event_obj.created_at
                )
            )

    return schemas.ProcessFrameResponse(
        session_id=session_id,
        status=session_status,
        detections_count=len(detections),
        events_generated=events_generated
    )

@router.post("/videos/process")
def process_video_clip(
    file: UploadFile = File(...),
    sample_fps: float = Query(1.0, description="Frame sampling rate in FPS"),
    max_phone_limit: Optional[float] = Query(None, description="Max phone usage limit in seconds"),
    max_missing_limit: Optional[float] = Query(None, description="Max missing candidate limit in seconds")
):
    """
    Uploads a video file clip, processes frames, calculates violation time intervals,
    checks duration limits, and returns analysis report JSON.
    """
    temp_dir = tempfile.mkdtemp(prefix="video_analysis_")
    try:
        temp_video_path = os.path.join(temp_dir, file.filename or "uploaded_video.mp4")
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        output_dir = os.path.join(settings.EVIDENCE_DIR, f"video_{os.path.splitext(file.filename or 'clip')[0]}")
        
        custom_limits = {}
        if max_phone_limit is not None:
            custom_limits["PHONE_DETECTED"] = max_phone_limit
        if max_missing_limit is not None:
            custom_limits["NO_PERSON_DETECTED"] = max_missing_limit

        report = VideoProcessor.process_video_file(
            video_path=temp_video_path,
            output_dir=output_dir,
            sample_fps=sample_fps,
            custom_limits=custom_limits if custom_limits else None
        )

        return report

    except Exception as e:
        logger.error(f"Error processing video upload {file.filename}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Video analysis failed: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/sessions/{session_id}/events", response_model=schemas.SessionEventsResponse)
def get_session_events(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all flagged events and evidence records for a session.
    """
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    events = db.query(EventModel).filter(EventModel.session_id == session_id).all()
    event_responses = []

    for ev in events:
        evidence_path = ev.evidence.file_path if ev.evidence else None
        event_responses.append(
            schemas.EventResponse(
                event_id=ev.id,
                event_type=ev.event_type,
                rule_triggered=ev.rule_triggered,
                confidence=ev.confidence,
                evidence_path=evidence_path,
                created_at=ev.created_at
            )
        )

    return schemas.SessionEventsResponse(
        session_id=session_id,
        total_events=len(event_responses),
        events=event_responses
    )

@router.post("/sessions/{session_id}/end", response_model=schemas.SessionResponse)
def end_session(session_id: str, db: Session = Depends(get_db)):
    """
    Ends an active monitoring session.
    """
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    session_obj.status = "COMPLETED"
    db.commit()
    db.refresh(session_obj)

    logger.info(f"Ended session {session_id}")
    return schemas.SessionResponse(
        session_id=session_obj.id,
        user_id=session_obj.user_id,
        status=session_obj.status,
        created_at=session_obj.created_at
    )
