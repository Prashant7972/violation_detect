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

---

## 9. Component Responsibilities
- **Video Sampler (`cv2.VideoCapture`)**: Reads video file metadata, steps through video frames at configured sample rates, and handles timestamp conversions (`HH:MM:SS.mmm`).
- **AI Detection Engine (`AIDetector`)**: Runs object predictions on sampled frames, applies YOLOv8 or OpenCV cascades, and deduplicates person bounding boxes via IoU NMS.
- **Rule Engine (`RuleEngine`)**: Matches observations against compliance rules (`PHONE_DETECTED`, `MULTIPLE_PERSONS`, `NO_PERSON_DETECTED`, `UNAUTHORIZED_DEVICE`).
- **Time Interval Tracker**: Aggregates consecutive violation frames into distinct intervals (`start_timestamp`, `end_timestamp`, `duration_seconds`) and computes cumulative durations.
- **Limit Enforcer**: Compares cumulative violation durations against configured thresholds and flags `PASSED` / `FAILED` overall status.
- **Evidence Snapshotter**: Annotates violation frames with red bounding boxes and writes keyframe JPEG files to disk.

---
