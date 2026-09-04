## 4. Functional Requirements
- **FR-1**: User can supply a video file input (`.mp4`, `.webm`, `.avi`, `.mov`) via CLI or HTTP API endpoint.
- **FR-2**: System extracts native FPS, total frame count, and video clip duration.
- **FR-3**: If Student ID is not provided by admin, system auto-generates next serial ID (`STU-001`, `STU-002`, ...).
- **FR-4**: AI Detector predicts object bounding boxes and confidence scores (YOLOv8 / OpenCV cascades).
- **FR-5**: Rule Engine evaluates compliance rules (`PHONE_DETECTED`, `MULTIPLE_PERSONS`, `NO_PERSON_DETECTED`, `UNAUTHORIZED_DEVICE`).
- **FR-6**: Limit Engine compares cumulative violation duration against configured thresholds (`PASSED` / `FAILED`).
- **FR-7**: System Reset functionality purges all records and deletes evidence files.

---

---

## 5. Non-Functional Requirements
- **NFR-1 (Performance)**: Video file analysis processing speed `>2x` realtime on CPU.
- **NFR-2 (Accuracy)**: Non-Maximum Suppression (NMS) and IoU/IoA box merging to prevent duplicate candidate counting.
- **NFR-3 (Maintainability)**: Clear separation of `VideoProcessor`, `AIDetector`, `RuleEngine`, `endpoints`, and database ORM models.

---
