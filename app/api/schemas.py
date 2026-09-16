import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

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

# Pre-Authentication Identity Verification & Login Schemas
class VerifyIDRequest(BaseModel):
    username: Optional[str] = Field(None, description="Candidate Username / Student ID")
    email: Optional[str] = Field("candidate@example.com", description="Candidate Email Address (Optional)")
    document_id_b64: str = Field(..., description="Base64 encoded Document ID Photo")
    live_selfie_b64: str = Field(..., description="Base64 encoded Live Selfie Photo")
    document_type: Optional[str] = Field("aadhaar", description="Document type: 'aadhaar', 'pan', 'driving_license', 'passport'")

class VerifyIDResponse(BaseModel):
    status: str = "VERIFIED"
    match_confidence: float = Field(..., description="Facial match confidence score (>= 0.70 required)")
    match_percentage: str = Field(..., description="Facial match percentage (e.g. 94.5%)")
    document_type: Optional[str] = "aadhaar"
    email_sent_to: str
    password_issued: Optional[str] = None
    document_status: Optional[str] = "VALID"
    document_warning: Optional[str] = None
    document_validation: Optional[Dict[str, Any]] = None
    message: str

class LoginRequest(BaseModel):
    username: str = Field(..., description="Candidate Username")
    password: Optional[str] = Field("", description="Authentication Password (Optional if auto-progressing)")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    status: str = "AUTHENTICATED"
    email_sent: bool = True
    email_sent_to: Optional[str] = None
    message: str = "Credentials matched successfully. Access token issued and confirmation email dispatched to candidate."

class ConsentRequest(BaseModel):
    session_token: str
    consent_agreed: bool = Field(..., description="Must be True to proceed")

class ConsentResponse(BaseModel):
    status: str = "CONSENT_RECORDED"
    message: str
    timestamp: datetime.datetime

class ReadinessCheckRequest(BaseModel):
    session_token: str
    media_api_supported: bool = True
    file_api_supported: bool = True
    screen_resolution_valid: bool = True
    identity_photo_provided: bool = True

class ReadinessCheckResponse(BaseModel):
    status: str = "READY_FOR_SESSION"
    message: str
    checks_passed: Dict[str, bool]

class CandidateCredentialsResponse(BaseModel):
    username: str
    email: str
    password: str
    status: str = "ISSUED"

class ExamSubmissionRequest(BaseModel):
    student_id: str = Field(..., description="Candidate username or ID")
    student_name: Optional[str] = Field("Candidate", description="Full name")
    exam_id: Optional[str] = Field("MIDTERM-2026", description="Exam ID")
    score: int = Field(..., description="Calculated test score")
    total_questions: int = Field(5, description="Total questions in exam")
    answers: Dict[str, Any] = Field(default_factory=dict, description="Submitted answers")
    face_match_percentage: Optional[str] = Field("93.8%", description="Face match percentage")
    proctoring_status: Optional[str] = Field("PASSED", description="Proctoring verdict")
    phone_violations: Optional[float] = Field(0.0, description="Phone violation seconds")
    multiple_person_violations: Optional[float] = Field(0.0, description="Multiple persons violation seconds")

class ExamSubmissionResponse(BaseModel):
    submission_id: str
    student_id: str
    exam_id: str
    score: int
    total_questions: int
    percentage: float
    proctoring_status: str
    overall_status: str
    certificate_id: str
    submitted_at: datetime.datetime
    message: str

class ValidateDocumentRequest(BaseModel):
    document_id_b64: str = Field(..., description="Base64 encoded document ID photo")
    document_type: Optional[str] = Field("aadhaar", description="Selected document type: aadhaar, pan, driving_license, passport")
    selected_type: Optional[str] = Field(None, description="Alias for document_type")

    @model_validator(mode="before")
    @classmethod
    def resolve_doc_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            chosen = data.get("selected_type") or data.get("document_type") or "aadhaar"
            data["document_type"] = chosen
            data["selected_type"] = chosen
        return data

class ValidateDocumentResponse(BaseModel):
    status: str = Field(..., description="VALID, MISMATCH, INVALID, BLURRY, or NOT_AN_ID")
    is_match: bool
    detected_type: str
    selected_type: str
    detected_label: str
    selected_label: str
    warning_message: str
    clarity_score: float
    checks: Dict[str, Any]

class ScanLiveFrameRequest(BaseModel):
    student_id: Optional[str] = Field("STU-001", description="Candidate / Student ID")
    frame_data: str = Field(..., description="Base64 encoded webcam JPEG image string")

class ScanLiveFrameResponse(BaseModel):
    status: str = "CLEAN"
    phone_detected: bool = False
    laptop_detected: bool = False
    multiple_persons: bool = False
    person_present: bool = True
    detections: List[Dict[str, Any]] = []
    violations: List[str] = []
    evidence_url: Optional[str] = None
    summary_message: str
    warning_chat_message: Optional[str] = None


class ChatQueryRequest(BaseModel):
    query: str = Field(..., description="Candidate question regarding policies or setup")
    student_id: Optional[str] = Field("STU-001", description="Candidate identifier")


class ChatQueryResponse(BaseModel):
    response: str
    citations: List[str] = []
    suggested_questions: List[str] = []
    is_warning: bool = False


class ViolationWarningRequest(BaseModel):
    violation_type: str = Field(..., description="Type of violation: PHONE, LAPTOP, DOUBLE_PERSON, etc.")
    student_id: Optional[str] = Field("STU-001", description="Candidate identifier")


class ViolationWarningResponse(BaseModel):
    warning_title: str
    warning_message: str
    citation: str
    can_terminate: bool = False
    student_id: str = "STU-001"
    is_warning: bool = True


class CompanyPolicyItem(BaseModel):
    id: str
    name: str
    industry: str
    strictness: str
    description: str


class CompanyPolicyListResponse(BaseModel):
    active_company_id: str
    active_company_name: str
    companies: List[CompanyPolicyItem]


class SetActiveCompanyRequest(BaseModel):
    company_id: str


class AdminPolicyBreachItem(BaseModel):
    timestamp: str
    student_id: str
    company_id: str
    company_name: str
    violation_type: str
    policy_clause: str
    severity: str
    rule_description: str
    evidence_url: str
    admin_action_recommended: str


class AdminPolicyBreachesResponse(BaseModel):
    total_breaches: int
    active_company: str
    breaches: List[AdminPolicyBreachItem]
