# PROJECT DOCUMENTATION: AI Video Clip Analysis & Event Monitoring System

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
13. [API Design](#13-api-design)
14. [Video File Processing Workflow](#14-video-file-processing-workflow)
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
The **AI Video Clip Analysis & Event Monitoring System** is an automated video analysis solution designed for proctoring, compliance auditing, and security surveillance. The system ingests recorded video files (`.mp4`, `.webm`, `.avi`), samples frames at configurable intervals, evaluates object and behavioral anomalies via AI vision models, calculates exact violation time intervals (start/end timestamp, duration), checks cumulative violation times against configured thresholds, extracts evidence keyframes, and logs security events to a database or structured JSON report.

---

## 2. Problem Statement
Manual supervision of video recordings (e.g., remote exam recordings, workplace safety footage) is time-consuming, expensive, and subject to human oversight. Automated video stream analysis requires frame sampling, deterministic AI object/behavior recognition, time interval calculation (e.g. how many seconds a cell phone was visible), threshold limit enforcement, and visual keyframe evidence extraction.

---

## 3. Objectives
- **Sub-Second Frame Analysis**: Fast frame sampling and batch inference over video files.
- **Exact Violation Duration Metrics**: Compute start timestamp, end timestamp, and duration (in seconds) for every rule violation interval.
- **Threshold Limit Enforcement**: Flag sessions where cumulative violation time exceeds defined limits (e.g., cell phone usage > 5.0s).
- **Keyframe Evidence Extraction**: Save annotated keyframe images with bounding boxes for all flagged violation intervals.
- **Dual CLI & API Interfaces**: Support standalone CLI execution (`process_video.py`) and HTTP API uploads (`POST /api/v1/videos/process`).

---

## 4. Functional Requirements
- **FR-1**: User can supply a video file input (`.mp4`, `.webm`, `.avi`, `.mov`) via CLI or HTTP API endpoint.
- **FR-2**: System extracts native FPS, total frame count, and video clip duration.
- **FR-3**: System samples frames at a configurable sampling rate (default 1.0 FPS).
- **FR-4**: AI Detector predicts object bounding boxes and confidence scores (YOLOv8 / OpenCV cascades).
- **FR-5**: Rule Engine evaluates compliance rules (`PHONE_DETECTED`, `MULTIPLE_PERSONS`, `NO_PERSON_DETECTED`, `UNAUTHORIZED_DEVICE`).
- **FR-6**: Time Interval Processor aggregates contiguous violation frames into start/end timestamp intervals and calculates total duration seconds.
- **FR-7**: Limit Engine compares cumulative violation duration against configured thresholds and flags limit violations (`PASSED` / `FAILED`).
- **FR-8**: Evidence Service extracts annotated JPEG keyframe snapshots with bounding box highlights and saves them to disk.

---

## 5. Non-Functional Requirements
- **NFR-1 (Performance)**: Video file analysis processing speed `>2x` realtime on CPU for sampled 1 FPS streams.
- **NFR-2 (Accuracy)**: Non-Maximum Suppression (NMS) and IoU/IoA box merging to prevent duplicate candidate counting.
- **NFR-3 (Maintainability)**: Modular separation of `VideoProcessor`, `AIDetector`, `RuleEngine`, and API routes.
- **NFR-4 (Security)**: Ephemeral video frame buffer processing; persistent storage restricted to extracted keyframe evidence.

---

## 6. User Workflow

```
USER
  │
  ├─► Provides Video Clip Input (e.g. video.mp4)
  │
  ├─► Configures Sampling FPS (e.g. 1 FPS) & Duration Limits
  │
  ├─► Executes CLI script `python process_video.py --input video.mp4`
  │   OR uploads file via API `POST /api/v1/videos/process`
  │
  ├─► System processes video clip frame-by-frame
  │
  ├─► System calculates violation time intervals & cumulative durations
  │
  ├─► System extracts annotated evidence keyframe images
  │
  └─► Receives structured JSON Analysis Report & Evidence directory
```

---

## 7. Complete System Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Input Video │────►│ Frame        │────►│ AI Model     │────►│ Rule Engine  │
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
 │ CLI Script /   │  HTTP / CLI│  │ cv2.Video  │─────►│ Frame Sampler  │  │
 │ REST API Input │───────────┼─►│ Capture    │      │ (1 FPS)        │  │
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
                         │ Extracted Keyframe      │                     │ Analysis Report         │
                         │ Evidence (/evidence/*)  │                     │ (analysis_report.json)  │
                         └─────────────────────────┘                     └─────────────────────────┘
```

---

## 9. Component Responsibilities
- **Video Sampler (`cv2.VideoCapture`)**: Reads video file metadata, steps through video frames at configured sample rates, and handles timestamp conversions (`HH:MM:SS.mmm`).
- **AI Detection Engine (`AIDetector`)**: Runs object predictions on sampled frames, applies YOLOv8 or OpenCV cascades, and deduplicates person bounding boxes via IoU NMS.
- **Rule Engine (`RuleEngine`)**: Matches observations against compliance rules (`PHONE_DETECTED`, `MULTIPLE_PERSONS`, `NO_PERSON_DETECTED`, `UNAUTHORIZED_DEVICE`).
- **Time Interval Tracker**: Aggregates consecutive violation frames into distinct intervals (`start_timestamp`, `end_timestamp`, `duration_seconds`) and computes cumulative durations.
- **Limit Enforcer**: Compares cumulative violation durations against configured thresholds and flags `PASSED` / `FAILED` overall status.
- **Evidence Snapshotter**: Annotates violation frames with red bounding boxes and writes keyframe JPEG files to disk.

---

## 10. Technology Stack
- **Language**: Python 3.11+
- **Video Decoding**: OpenCV (`opencv-python-headless`)
- **AI Detection**: Ultralytics YOLOv8 (PyTorch) with multi-cascade fallback
- **Web API**: FastAPI & Uvicorn
- **Data Validation & Schemas**: Pydantic v2
- **Testing**: Pytest & FastAPI TestClient

---

## 11. Project Folder Structure

```
ai_detection_system/
├── PROJECT_DOCUMENTATION.md
├── process_video.py              # Standalone CLI Video Processor Script
├── docs/
│   ├── 01-project-overview.md
│   ├── 02-requirements.md
│   ├── 03-user-workflow.md
│   ├── 04-system-workflow.md
│   ├── 05-architecture.md
│   ├── 06-frontend.md
│   ├── 07-backend.md
│   ├── 08-video-processing.md
│   ├── 09-ai-detection.md
│   ├── 10-detection-rules.md
│   ├── 11-database.md
│   ├── 12-api.md
│   ├── 13-evidence-storage.md
│   ├── 14-security-privacy.md
│   ├── 15-testing.md
│   ├── 16-performance.md
│   ├── 17-redis-workers.md
│   ├── 18-docker.md
│   ├── 19-cloud-migration.md
│   └── 20-operations.md
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── endpoints.py
│   │   └── schemas.py
│   ├── db/
│   │   ├── session.py
│   │   └── models.py
│   └── ai/
│       ├── detector.py
│       ├── rule_engine.py
│       └── video_processor.py   # Core Video Analysis Library
├── evidence/                    # Extracted evidence keyframes
├── tests/
│   ├── test_rule_engine.py
│   ├── test_api.py
│   └── test_video_processor.py
└── requirements.txt
```

---

## 12. Database Design
Relational tables (`sessions`, `events`, `evidence`) persist session metadata, recorded violation events, and extracted evidence keyframe paths.

---

## 13. API Design

### Process Video Upload
- **HTTP Method**: `POST`
- **Path**: `/api/v1/videos/process`
- **Request**: Multipart Form Data (`file: UploadFile`, `sample_fps: float`, `max_phone_limit: float`)
- **Response Body (HTTP 200 OK)**:
```json
{
  "video_file": "candidate_exam.mp4",
  "video_metadata": {
    "native_fps": 30.0,
    "total_frames": 3600,
    "duration_seconds": 120.0,
    "duration_formatted": "00:02:00.000"
  },
  "overall_status": "FAILED",
  "overall_limit_exceeded": true,
  "cumulative_durations": {
    "PHONE_DETECTED": 14.5,
    "NO_PERSON_DETECTED": 2.0
  },
  "limit_enforcement": {
    "PHONE_DETECTED": {
      "cumulative_duration_seconds": 14.5,
      "limit_threshold_seconds": 5.0,
      "limit_exceeded": true
    }
  },
  "violation_intervals": [
    {
      "event_type": "PHONE_DETECTED",
      "rule_triggered": "IF object IN ['cell phone'] AND confidence >= 0.45",
      "start_timestamp": "00:00:12.000",
      "end_timestamp": "00:00:26.500",
      "duration_seconds": 14.5,
      "peak_confidence": 0.91,
      "evidence_file": "/evidence/video_candidate_exam/evidence_phone_detected_12000ms.jpg"
    }
  ]
}
```

---

## 14. Video File Processing Workflow
1. `VideoProcessor.process_video_file()` opens input video file with `cv2.VideoCapture`.
2. Extracts native FPS and total frames to compute video duration.
3. Steps through frames using `frame_idx % frame_step == 0`.
4. Decodes image array and calculates current video timestamp (`HH:MM:SS.mmm`).
5. Passes frame to `AIDetector.detect()` and `RuleEngine.evaluate()`.

---

## 15. Backend Workflow
1. API router accepts `UploadFile`.
2. Saves file to temporary path.
3. Calls `VideoProcessor`.
4. Returns report JSON and serves evidence keyframes under `/evidence/` endpoint.

---

## 16. Time Interval & Duration Tracking Workflow
- **Interval Creation**: When a rule violation starts on a sampled frame, a new interval object is created with `start_timestamp`.
- **Interval Extension**: If the violation continues on consecutive sampled frames, `end_timestamp` is updated.
- **Interval Close**: When the violation ceases, duration is calculated:
  $$\text{Duration} = (\text{End\_Time} - \text{Start\_Time}) + \frac{1.0}{\text{Sample\_FPS}}$$
- **Cumulative Duration**: Sum of all interval durations per event type across the video clip.

---

## 17. AI Detection Workflow
- Uses YOLOv8 nano / PyTorch model with `conf=0.35`.
- Deduplicates person detections via `_merge_duplicate_person_boxes()`.

---

## 18. Detection Rules & Time Limits

| Rule ID | Event Type | Condition | Default Time Limit |
|---|---|---|---|
| `R-01` | `PHONE_DETECTED` | `IF object IN ['cell phone'] AND confidence >= 0.45` | **5.0 Seconds** |
| `R-02` | `MULTIPLE_PERSONS` | `IF count(person) > 1 AND confidence >= 0.65` | **3.0 Seconds** |
| `R-03` | `NO_PERSON_DETECTED` | `IF count(person) == 0 AND confidence >= 0.65` | **10.0 Seconds** |
| `R-04` | `UNAUTHORIZED_DEVICE` | `IF object IN ['laptop', 'tv'] AND confidence >= 0.70` | **5.0 Seconds** |

---

## 19. Evidence Keyframe Extraction Workflow
- When an interval starts, the system annotates the BGR frame with red bounding boxes and label tags.
- The annotated image is saved as a JPEG snapshot: `/evidence/extracted_evidence/evidence_phone_detected_12000ms.jpg`.

---

## 20. Session Lifecycle
Video clip analysis transitions: `RECEIVED` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED` / `FAILED`.

---

## 21. Error Handling
- Invalid video file formats return HTTP 400.
- Corrupt frame reads are skipped gracefully without aborting analysis.

---

## 22. Logging
Structured JSON log outputs per processed video clip.

---

## 23. Security & Privacy
Video files are processed locally/ephemerally; extracted keyframe snapshots stored with session-scoped access.

---

## 24. Performance & Scalability
Sampled 1 FPS frame extraction processes a 5-minute video clip in `<10 seconds` on standard CPU.

---

## 25. Testing Strategy
- Unit tests for `VideoProcessor` time interval calculations.
- CLI execution tests on synthetic test video files.
- FastAPI integration tests for `/api/v1/videos/process`.

---

## 26. Implementation Phases
- **Phase 1**: Video file processor core library (`video_processor.py`).
- **Phase 2**: CLI utility script (`process_video.py`).
- **Phase 3**: Video Upload API Endpoint (`POST /api/v1/videos/process`).
- **Phase 4**: Automated Pytest unit & integration test suite.

---

## 27. Development Checklist
- [x] Create project structure and master documentation
- [x] Build `VideoProcessor` interval duration tracker
- [x] Build CLI `process_video.py` script
- [x] Build `POST /api/v1/videos/process` API route
- [x] Run Pytest automated test suite
- [x] Perform end-to-end video clip analysis test

---

## 28. Local Setup
```bash
cd /home/prashant/.gemini/antigravity/scratch/ai_detection_system
source venv/bin/activate
pip install -r requirements.txt
```

---

## 29. Running the Application

### 1. Run CLI Video Processor Script
```bash
python process_video.py --input sample_video.mp4 --sample-fps 1.0 --max-phone 5.0
```

### 2. Run API Server
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 30. Future Redis Architecture
Redis Streams for background video file processing queues.

---

## 31. Dockerization Plan
Docker container with OpenCV, PyTorch, and FastAPI.

---

## 32. Cloud Migration Plan
AWS S3 video storage & AWS ECS worker nodes.

---

## 33. Production Architecture
Distributed microservices architecture.

---

## 34. Monitoring
Prometheus metrics tracking video processing duration and limit violations.

---

## 35. Maintenance
Retention policies for processed video outputs and evidence snapshots.

---

## 36. Final End-to-End Workflow

```
[USER / CLIENT]
  │  Provides video clip: video.mp4
  ▼
[CLI / REST API]
  │  python process_video.py --input video.mp4  OR  POST /api/v1/videos/process
  ▼
[VIDEO SAMPLER]
  │  cv2.VideoCapture  ──►  Sample frames at 1 FPS  ──►  Compute Timestamps
  ▼
[AI DETECTOR & RULE ENGINE]
  │  YOLOv8 Inference  ──►  Evaluate Detections against Rules
  ▼
[TIME INTERVAL & LIMIT ENGINE]
  │  Group frames into intervals (start_time, end_time, duration_seconds)
  │  Sum cumulative durations & check limit thresholds (PHONE_DETECTED > 5.0s?)
  ▼
[EVIDENCE EXTRACTOR]
  │  Annotate frames with bounding boxes  ──►  Save evidence JPEGs to disk
  ▼
[OUTPUT REPORT]
  │  Generates JSON Report & displays summary with PASSED / FAILED status
  ▼
[AUDITOR / USER]
```
