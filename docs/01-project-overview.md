## 1. Project Overview
The **AI Video Clip Analysis & Event Monitoring System** is an automated video analysis solution designed for proctoring, compliance auditing, and security surveillance. The system ingests candidate video files (`.mp4`, `.webm`, `.avi`), samples frames at configurable intervals, evaluates object and behavioral anomalies via AI vision models, calculates exact violation time intervals, tracks cumulative violation durations, enforces limit thresholds, extracts evidence keyframes, and indexes all submissions by Candidate/Student ID.

---

---

## 2. Problem Statement
Manual supervision of video recordings (e.g., remote exam recordings, workplace safety footage) is time-consuming and prone to oversight. Automated video stream analysis requires frame sampling, deterministic AI object/behavior recognition, time interval calculation (e.g. how many seconds a cell phone was visible), threshold limit enforcement, serial candidate indexing (`STU-001`, `STU-002`), and complete database reset mechanisms.

---

---

## 3. Objectives
- **Sub-Second Frame Analysis**: Fast frame sampling and batch inference over video files.
- **Serial Candidate Indexing**: Automatically generate sequential zero-padded Student IDs (`STU-001`, `STU-002`, `STU-003`, ...) when omitted by an admin.
- **System Reset & Storage Purging**: Provide REST API (`POST /api/v1/system/reset`) and UI options to clear all database tables and evidence files on demand.
- **Exact Violation Duration Metrics**: Compute start timestamp, end timestamp, and duration (in seconds) for every rule violation interval.
- **Threshold Limit Enforcement**: Flag sessions where cumulative violation time exceeds defined limits (e.g., cell phone usage > 5.0s).

---
