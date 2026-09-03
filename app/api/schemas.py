import datetime
from typing import List, Optional
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
