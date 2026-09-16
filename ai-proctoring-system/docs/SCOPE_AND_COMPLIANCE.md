# Scope, Security & Compliance Specification

## 1. Phase-1 Functional Scope
1. **Identity Verification**: Pre-exam biometric face verification comparing government photo ID with live webcam capture, with human review fallback for borderline cases.
2. **Continuous Multi-Angle Ingestion**: Ingesting primary webcam feed, candidate mobile secondary camera, and microphone audio.
3. **Automated Anomaly Detection**:
   - Face absence (`NO_FACE_DETECTED`)
   - Extra individuals (`MULTIPLE_FACES_DETECTED`)
   - Identity mismatch (`FACE_MISMATCH`)
   - Prohibited hardware (smartphones, auxiliary screens, earbuds, physical notes)
   - Audio anomalies (whispering, multiple voices, dictation)
4. **Explainable Evidence Timeline**: Immutable audit records containing timestamp, bounding boxes, severity, confidence, and reasoning chains.
5. **Human-in-the-Loop (HITL) Controls**: Low-latency proctor review portal for high-risk flags, dual-stream replay, and manual confirmation before any penalty.

## 2. Non-Negotiable Compliance Constraints
- **Encryption at Rest & In Transit**: AES-256 / SSE-KMS for all stored media; TLS 1.3 for all live streams.
- **Tenant Isolation**: Namespace partitioning strictly enforced: `tenant_id:organization_id:session_id`.
- **Ephemeral Processing**: Unflagged raw frames are discarded immediately after inference; only violation snapshots are retained in secure storage.
- **Human Oversight Guarantee**: No automated AI model is permitted to autonomously terminate an exam. All `HIGH` or `CRITICAL` flags trigger human review.
