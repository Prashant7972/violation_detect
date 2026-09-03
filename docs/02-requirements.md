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

---

## 5. Non-Functional Requirements
- **NFR-1 (Performance)**: Video file analysis processing speed `>2x` realtime on CPU for sampled 1 FPS streams.
- **NFR-2 (Accuracy)**: Non-Maximum Suppression (NMS) and IoU/IoA box merging to prevent duplicate candidate counting.
- **NFR-3 (Maintainability)**: Modular separation of `VideoProcessor`, `AIDetector`, `RuleEngine`, and API routes.
- **NFR-4 (Security)**: Ephemeral video frame buffer processing; persistent storage restricted to extracted keyframe evidence.

---
