## 1. Project Overview
The **AI Video Clip Analysis & Event Monitoring System** is an automated video analysis solution designed for proctoring, compliance auditing, and security surveillance. The system ingests recorded video files (`.mp4`, `.webm`, `.avi`), samples frames at configurable intervals, evaluates object and behavioral anomalies via AI vision models, calculates exact violation time intervals (start/end timestamp, duration), checks cumulative violation times against configured thresholds, extracts evidence keyframes, and logs security events to a database or structured JSON report.

---

---

## 2. Problem Statement
Manual supervision of video recordings (e.g., remote exam recordings, workplace safety footage) is time-consuming, expensive, and subject to human oversight. Automated video stream analysis requires frame sampling, deterministic AI object/behavior recognition, time interval calculation (e.g. how many seconds a cell phone was visible), threshold limit enforcement, and visual keyframe evidence extraction.

---

---

## 3. Objectives
- **Sub-Second Frame Analysis**: Fast frame sampling and batch inference over video files.
- **Exact Violation Duration Metrics**: Compute start timestamp, end timestamp, and duration (in seconds) for every rule violation interval.
- **Threshold Limit Enforcement**: Flag sessions where cumulative violation time exceeds defined limits (e.g., cell phone usage > 5.0s).
- **Keyframe Evidence Extraction**: Save annotated keyframe images with bounding boxes for all flagged violation intervals.
- **Dual CLI & API Interfaces**: Support standalone CLI execution (`process_video.py`) and HTTP API uploads (`POST /api/v1/videos/process`).

---
