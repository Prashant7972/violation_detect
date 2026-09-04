# PROJECT DOCUMENTATION: AI Video File Analysis & Event Monitoring System

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Objectives](#3-objectives)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [User Workflow](#6-user-workflow)
7. [Complete System Workflow](#7-complete-system-workflow)
8. [System Architecture](#8-system-architecture)
9. [Component Responsibilities](#9-component-responsibilities)
10. [Technology Stack](#10-technology-stack)
11. [Project Folder Structure](#11-project-folder-structure)
12. [Database Design](#12-database-design)
13. [API Design & System Reset](#13-api-design--system-reset)
14. [Serial Student ID Generation](#14-serial-student-id-generation)
15. [Backend Workflow](#15-backend-workflow)
16. [Time Interval & Duration Tracking Workflow](#16-time-interval--duration-tracking-workflow)
17. [AI Detection Workflow](#17-ai-detection-workflow)
18. [Detection Rules & Time Limits](#18-detection-rules--time-limits)
19. [Evidence Keyframe Extraction Workflow](#19-evidence-keyframe-extraction-workflow)
20. [Session Lifecycle](#20-session-lifecycle)
21. [Error Handling](#21-error-handling)
22. [Logging](#22-logging)
23. [Security & Privacy](#23-security--privacy)
24. [Performance & Scalability](#24-performance--scalability)
25. [Testing Strategy](#25-testing-strategy)
26. [Implementation Phases](#26-implementation-phases)
27. [Development Checklist](#27-development-checklist)
28. [Local Setup](#28-local-setup)
29. [Running the Application](#29-running-the-application)
30. [Future Redis Architecture](#30-future-redis-architecture)
31. [Dockerization Plan](#31-dockerization-plan)
32. [Cloud Migration Plan](#32-cloud-migration-plan)
33. [Production Architecture](#33-production-architecture)
34. [Monitoring](#34-monitoring)
35. [Maintenance](#35-maintenance)
36. [Final End-to-End Workflow](#36-final-end-to-end-workflow)

---

## 1. Project Overview
The **AI Video Clip Analysis & Event Monitoring System** is an automated video analysis solution designed for proctoring, compliance auditing, and security surveillance. The system ingests candidate video files (`.mp4`, `.webm`, `.avi`), samples frames at configurable intervals, evaluates object and behavioral anomalies via AI vision models, calculates exact violation time intervals, tracks cumulative violation durations, enforces limit thresholds, extracts evidence keyframes, and indexes all submissions by Candidate/Student ID.

---

## 2. Problem Statement
Manual supervision of video recordings (e.g., remote exam recordings, workplace safety footage) is time-consuming and prone to oversight. Automated video stream analysis requires frame sampling, deterministic AI object/behavior recognition, time interval calculation (e.g. how many seconds a cell phone was visible), threshold limit enforcement, serial candidate indexing (`STU-001`, `STU-002`), and complete database reset mechanisms.

---

## 3. Objectives
- **Sub-Second Frame Analysis**: Fast frame sampling and batch inference over video files.
- **Serial Candidate Indexing**: Automatically generate sequential zero-padded Student IDs (`STU-001`, `STU-002`, `STU-003`, ...) when omitted by an admin.
- **System Reset & Storage Purging**: Provide REST API (`POST /api/v1/system/reset`) and UI options to clear all database tables and evidence files on demand.
- **Exact Violation Duration Metrics**: Compute start timestamp, end timestamp, and duration (in seconds) for every rule violation interval.
- **Threshold Limit Enforcement**: Flag sessions where cumulative violation time exceeds defined limits (e.g., cell phone usage > 5.0s).

---

## 4. Functional Requirements
- **FR-1**: User can supply a video file input (`.mp4`, `.webm`, `.avi`, `.mov`) via CLI or HTTP API endpoint.
- **FR-2**: System extracts native FPS, total frame count, and video clip duration.
- **FR-3**: If Student ID is not provided by admin, system auto-generates next serial ID (`STU-001`, `STU-002`, ...).
- **FR-4**: AI Detector predicts object bounding boxes and confidence scores (YOLOv8 / OpenCV cascades).
- **FR-5**: Rule Engine evaluates compliance rules (`PHONE_DETECTED`, `MULTIPLE_PERSONS`, `NO_PERSON_DETECTED`, `UNAUTHORIZED_DEVICE`).
- **FR-6**: Limit Engine compares cumulative violation duration against configured thresholds (`PASSED` / `FAILED`).
- **FR-7**: System Reset functionality purges all records and deletes evidence files.

---

## 5. Non-Functional Requirements
- **NFR-1 (Performance)**: Video file analysis processing speed `>2x` realtime on CPU.
- **NFR-2 (Accuracy)**: Non-Maximum Suppression (NMS) and IoU/IoA box merging to prevent duplicate candidate counting.
- **NFR-3 (Maintainability)**: Clear separation of `VideoProcessor`, `AIDetector`, `RuleEngine`, `endpoints`, and database ORM models.

---

## 6. User Workflow

```
USER / ADMIN
  │
  ├─► Provides Video Clip Input (e.g. candidate_video.mp4)
  │
  ├─► Leaves Student ID blank or provides custom Student ID (e.g. STU-001)
  │
  ├─► Submits video file via CLI `python process_video.py` or Web UI Dashboard
  │
  ├─► System processes video clip & calculates violation time intervals
  │
  ├─► System stores evidence in candidate-isolated directory `/evidence/candidates/STU-001/`
  │
  └─► Admin can view Candidate Directory or click "Reset All Data" to start clean
```

---

## 7. Complete System Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Input Video │────►│ Serial ID    │────►│ AI Model     │────►│ Rule Engine  │
│ File (.mp4) │     │ Sampler      │     │ Inference    │     │ Evaluation   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Analysis    │◄────│ Evidence     │◄────│ Limit        │◄────│ Time         │
│ Report JSON │     │ Snapshotter  │     │ Enforcer     │     │ Intervalizer │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 8. System Architecture

```
                               ┌──────────────────────────────────────────┐
                               │           Video File Processor           │
                               │                                          │
 ┌────────────────┐            │  ┌────────────┐      ┌────────────────┐  │
 │ CLI Script /   │  HTTP / CLI│  │ Serial ID  │─────►│ Frame Sampler  │  │
 │ REST API Input │───────────┼─►│ Generator  │      │ (1 FPS)        │  │
 └────────────────┘            │  └────────────┘      └───────┬────────┘  │
                               │                              │           │
                               │                              ▼           │
                               │                      ┌────────────────┐  │
                               │                      │ AI Detection   │  │
                               │                      │ Engine (YOLO)  │  │
                               │                      └───────┬────────┘  │
                               │                              │           │
                               │                              ▼           │
                               │                      ┌────────────────┐  │
                               │                      │ Rule Engine    │  │
                               │                      └───────┬────────┘  │
                               │                              │           │
                               │                              ▼           │
                               │                      ┌────────────────┐  │
                               │                      │ Interval & Time│  │
                               │                      │ Tracker        │  │
                               │                      └───────┬────────┘  │
                               └──────────────────────────────┼───────────┘
                                                              │
                                      ┌───────────────────────┴───────────────────────┐
                                      ▼                                               ▼
                         ┌─────────────────────────┐                     ┌─────────────────────────┐
                         │ Candidate Isolated      │                     │ Relational DB Record    │
                         │ Storage (/evidence/*)   │                     │ (CandidateSubmissions)  │
                         └─────────────────────────┘                     └─────────────────────────┘
```

---

## 9. Component Responsibilities
- **Serial Student ID Generator**: Scans existing submissions and assigns next sequential zero-padded ID (`STU-001`, `STU-002`, ...).
- **System Reset Service**: Handles `POST /api/v1/system/reset`, truncating all DB tables and removing file artifacts from disk.
- **Video Sampler**: Steps through video frames at configured sample rates (`1.0 FPS`).
- **AI Detection Engine (`AIDetector`)**: Predicts objects and deduplicates person bounding boxes.
- **Rule Engine (`RuleEngine`)**: Matches observations against compliance rules.
- **Limit Enforcer**: Compares cumulative violation durations against thresholds (`PASSED` / `FAILED`).

---

## 10. Technology Stack
- **Language**: Python 3.11+
- **Video Decoding**: OpenCV (`opencv-python-headless`)
- **AI Detection**: Ultralytics YOLOv8 (PyTorch) with multi-cascade fallback
- **Web API**: FastAPI & Uvicorn
- **ORM & DB**: SQLAlchemy & SQLite / PostgreSQL
- **Testing**: Pytest & FastAPI TestClient

---

## 11. Project Folder Structure

```
ai_detection_system/
├── PROJECT_DOCUMENTATION.md
├── process_video.py              # CLI Video Processor Script
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── endpoints.py          # API Routers (Includes Reset & Student ID routes)
│   │   └── schemas.py
│   ├── db/
│   │   ├── session.py
│   │   └── models.py             # ORM Models (CandidateSubmissionModel)
│   └── ai/
│       ├── detector.py
│       ├── rule_engine.py
│       └── video_processor.py   # Serial ID & Duration Processor
├── evidence/
│   └── candidates/               # Candidate-isolated storage
├── tests/
│   ├── test_candidate_submissions.py
│   ├── test_system_reset_and_serial.py
│   └── test_video_processor.py
└── requirements.txt
```

---

## 12. Database Design

### `candidate_submissions` Table
| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Record ID |
| `submission_id` | VARCHAR(64) | UNIQUE INDEX | Unique submission UUID |
| `student_id` | VARCHAR(64) | NOT NULL INDEX | Serial Student ID (e.g. `STU-001`) |
| `student_name` | VARCHAR(128) | NULLABLE | Candidate Full Name |
| `exam_id` | VARCHAR(64) | NULLABLE INDEX | Exam Identifier |
| `video_filename` | VARCHAR(256) | NOT NULL | Input Video Filename |
| `video_duration_seconds` | FLOAT | NOT NULL | Total Video Length (sec) |
| `overall_status` | VARCHAR(32) | NOT NULL | `PASSED` or `FAILED` |
| `phone_duration_seconds` | FLOAT | DEFAULT 0.0 | Total Phone Usage Time |
| `missing_duration_seconds` | FLOAT | DEFAULT 0.0 | Total Candidate Missing Time |
| `report_json_path` | VARCHAR(512) | NOT NULL | Report File Path |
| `evidence_dir_path` | VARCHAR(512) | NOT NULL | Evidence Folder Path |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Submission Timestamp |

---

## 13. API Design & System Reset

### 1. System Reset API
- **HTTP Method**: `POST`
- **Path**: `/api/v1/system/reset`
- **Response Body (HTTP 200 OK)**:
```json
{
  "status": "SUCCESS",
  "message": "All database records and evidence files have been purged. Serial counter reset to STU-001.",
  "next_student_id": "STU-001"
}
```

### 2. Get Next Serial Student ID API
- **HTTP Method**: `GET`
- **Path**: `/api/v1/system/next-student-id`
- **Response Body (HTTP 200 OK)**:
```json
{
  "next_student_id": "STU-001"
}
```

### 3. Process Video Upload API
- **HTTP Method**: `POST`
- **Path**: `/api/v1/videos/process`
- **Request Form Data**: `file: UploadFile`, `student_id: Optional[str]`, `student_name: Optional[str]`, `exam_id: Optional[str]`
- **Response Body**: Full JSON analysis report.

---

## 14. Serial Student ID Generation
When `student_id` is omitted or left blank:
1. System queries `CandidateSubmissionModel` for existing `student_id` records matching `STU-%`.
2. Extracts numeric suffixes, finds highest integer value ($N$).
3. Formats next ID as `STU-` + zero-padded integer ($N+1$).
4. Example sequence: `STU-001` $\rightarrow$ `STU-002` $\rightarrow$ `STU-003`.

---

## 15. Backend Workflow
1. Client calls `POST /api/v1/videos/process`.
2. Serial generator resolves `student_id`.
3. `VideoProcessor` executes frame sampling & rule evaluations.
4. Saves DB record and outputs JSON report.

---

## 16. Time Interval & Duration Tracking Workflow
Calculates duration for each continuous violation block:
$$\text{Duration} = (\text{End\_Time} - \text{Start\_Time}) + \frac{1.0}{\text{Sample\_FPS}}$$

---

## 17. AI Detection Workflow
YOLOv8 nano / PyTorch model (`conf=0.25`) with NMS deduplication.

---

## 18. Detection Rules & Time Limits

| Rule ID | Event Code | Condition | Default Limit |
|---|---|---|---|
| `R-01` | `PHONE_DETECTED` | `IF object IN ['cell phone'] AND confidence >= 0.30` | **5.0 Seconds** |
| `R-02` | `MULTIPLE_PERSONS` | `IF count(person) > 1 AND confidence >= 0.55` | **3.0 Seconds** |
| `R-03` | `NO_PERSON_DETECTED` | `IF count(person) == 0 AND confidence >= 0.55` | **10.0 Seconds** |

---

## 19. Evidence Keyframe Extraction Workflow
Saves annotated JPEG snapshot with red/orange bounding boxes: `/evidence/candidates/STU-001/<clip>/extracted_evidence/evidence_phone_12000ms.jpg`.

---

## 20. Session Lifecycle
Status transitions: `RECEIVED` $\rightarrow$ `PROCESSING` $\rightarrow$ `PASSED` / `FAILED`.

---

## 21. Error Handling
Invalid format returns HTTP 400; database rollback on transaction error.

---

## 22. Logging
Structured JSON logging for file processing and reset operations.

---

## 23. Security & Privacy
Isolated storage per student ID; reset API purges disk evidence cleanly.

---

## 24. Performance & Scalability
Sampled 1 FPS frame extraction processes 5-minute video in `<10 seconds`.

---

## 25. Testing Strategy
- Unit tests for serial Student ID generation (`STU-001`, `STU-002`).
- Integration tests for System Reset API (`POST /api/v1/system/reset`).

---

## 26. Implementation Phases
- **Phase 1**: Serial Student ID generator (`get_next_serial_student_id`).
- **Phase 2**: System Reset API endpoint (`POST /api/v1/system/reset`).
- **Phase 3**: Web UI Auto-Populated Serial ID & Reset button.
- **Phase 4**: Automated Pytest test suite execution.

---

## 27. Development Checklist
- [x] Create project structure and master documentation
- [x] Implement Serial Student ID generator
- [x] Implement System Reset API endpoint
- [x] Add Web UI Auto-Populated ID & Reset button
- [x] Run Pytest automated test suite

---

## 28. Local Setup
```bash
cd /home/prashant/.gemini/antigravity/scratch/ai_detection_system
source venv/bin/activate
pip install -r requirements.txt
```

---

## 29. Running the Application

### 1. Launch Web Application
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Reset All Data via API
```bash
curl -X POST http://localhost:8000/api/v1/system/reset
```

---

## 30. Future Redis Architecture
Redis Streams queue for high-volume video processing.

---

## 31. Dockerization Plan
Docker container with FastAPI, PyTorch, and OpenCV.

---

## 32. Cloud Migration Plan
AWS S3 & ECS worker nodes.

---

## 33. Production Architecture
Distributed microservice architecture.

---

## 34. Monitoring
Prometheus metrics tracking processing times and reset events.

---

## 35. Maintenance
Automated disk purging and log rotation.

---

## 36. Final End-to-End Workflow

```
[ADMIN / USER]
  │  Leaves Student ID blank or provides custom ID
  ▼
[SERIAL ID GENERATOR]
  │  Assigns next serial ID: STU-001  ──►  STU-002  ──►  STU-003
  ▼
[VIDEO SAMPLER & AI DETECTOR]
  │  Sample frames at 1 FPS  ──►  YOLOv8 Inference  ──►  Rule Evaluation
  ▼
[TIME TRACKER & LIMIT ENGINE]
  │  Calculate violation durations  ──►  Flag PASSED or FAILED
  ▼
[EXAMINER DIRECTORY & SYSTEM RESET]
  │  View candidate reports or click "Reset All Data" to clear storage
  ▼
[CLEAN STATE]
```
