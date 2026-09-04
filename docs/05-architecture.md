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

---

## 9. Component Responsibilities
- **Serial Student ID Generator**: Scans existing submissions and assigns next sequential zero-padded ID (`STU-001`, `STU-002`, ...).
- **System Reset Service**: Handles `POST /api/v1/system/reset`, truncating all DB tables and removing file artifacts from disk.
- **Video Sampler**: Steps through video frames at configured sample rates (`1.0 FPS`).
- **AI Detection Engine (`AIDetector`)**: Predicts objects and deduplicates person bounding boxes.
- **Rule Engine (`RuleEngine`)**: Matches observations against compliance rules.
- **Limit Enforcer**: Compares cumulative violation durations against thresholds (`PASSED` / `FAILED`).

---
