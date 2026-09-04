import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "user-456"}, description="Identifier of the user or candidate")

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_id: str
    status: str
    created_at: datetime.datetime

class FramePayloadRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID")
    timestamp: Optional[str] = Field(None, description="Client ISO timestamp")
    frame_data: str = Field(..., description="Base64 encoded JPEG image string")

class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: int
    event_type: str
    rule_triggered: str
    confidence: float
    evidence_path: Optional[str] = None
    created_at: datetime.datetime

class ProcessFrameResponse(BaseModel):
    session_id: str
    status: str
    detections_count: int
    events_generated: List[EventResponse]

class SessionEventsResponse(BaseModel):
    session_id: str
    total_events: int
    events: List[EventResponse]

class CandidateSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: str
    student_id: str
    student_name: Optional[str] = None
    exam_id: Optional[str] = None
    video_filename: str
    video_duration_seconds: float
    overall_status: str
    limit_exceeded: int
    phone_duration_seconds: float
    missing_duration_seconds: float
    multiple_persons_duration_seconds: float
    report_json_path: str
    evidence_dir_path: str
    created_at: datetime.datetime

class CandidateListResponse(BaseModel):
    total_submissions: int
    submissions: List[CandidateSubmissionResponse]

class BatchProcessResponse(BaseModel):
    total_files_processed: int
    submissions: List[Dict[str, Any]]
