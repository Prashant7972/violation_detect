## 28. Local Setup
```bash
cd /home/prashant/.gemini/antigravity/scratch/ai_detection_system
source venv/bin/activate
pip install -r requirements.txt
```

---

---

## 29. Running the Application
### 1. Launch Web Application
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Reset All Data via API
```bash
curl -X POST http://localhost:8000/api/v1/system/reset
```

---

---

## 34. Monitoring
Prometheus metrics tracking processing times and reset events.

---

---

## 35. Maintenance
Automated disk purging and log rotation.

---

---

## 36. Final End-to-End Workflow
```
[ADMIN / USER]
  │  Leaves Student ID blank or provides custom ID
  ▼
[SERIAL ID GENERATOR]
  │  Assigns next serial ID: STU-001  ──►  STU-002  ──►  STU-003
  ▼
[VIDEO SAMPLER & AI DETECTOR]
  │  Sample frames at 1 FPS  ──►  YOLOv8 Inference  ──►  Rule Evaluation
  ▼
[TIME TRACKER & LIMIT ENGINE]
  │  Calculate violation durations  ──►  Flag PASSED or FAILED
  ▼
[EXAMINER DIRECTORY & SYSTEM RESET]
  │  View candidate reports or click "Reset All Data" to clear storage
  ▼
[CLEAN STATE]
```
