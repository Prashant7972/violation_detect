# API Specification: AI Remote Proctoring System

## 1. Base URL & Versioning
- Version: `v1`
- Base Path: `/api/v1`

## 2. Endpoints Summary

### A. Candidate Session Lifecycle (`/api/v1/sessions`)
- `POST /api/v1/sessions/start`: Initializes a proctored exam session for a candidate.
- `POST /api/v1/sessions/{session_id}/frames`: Ingests primary and secondary camera frames with timestamps.
- `GET /api/v1/sessions/{session_id}/status`: Returns current candidate session risk score and warnings.

### B. Pre-Exam Identity Verification (`/api/v1/identity`)
- `POST /api/v1/identity/verify`: Submits photo ID and live selfie for biometric verification.
  - Returns: `status: VERIFIED | PENDING_HUMAN_REVIEW | REJECTED`, `match_confidence: float`.

### C. Proctor Review & Triage (`/api/v1/proctor`)
- `GET /api/v1/proctor/sessions`: Lists active exam sessions filtered by risk level.
- `GET /api/v1/proctor/sessions/{session_id}/timeline`: Returns immutable evidence timeline for an exam.
- `POST /api/v1/proctor/sessions/{session_id}/decision`: Proctor submits action (`APPROVE_IDENTITY`, `ISSUE_WARNING`, `TERMINATE_SESSION`).
- `WS /api/v1/proctor/stream`: Real-time WebSocket stream of live anomalies and risk alerts.
