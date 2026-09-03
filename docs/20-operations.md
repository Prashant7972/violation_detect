## 28. Local Setup
```bash
cd /home/prashant/.gemini/antigravity/scratch/ai_detection_system
source venv/bin/activate
pip install -r requirements.txt
```

---

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

---

## 34. Monitoring
Prometheus metrics tracking video processing duration and limit violations.

---

---

## 35. Maintenance
Retention policies for processed video outputs and evidence snapshots.

---

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
