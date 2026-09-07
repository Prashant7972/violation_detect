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
[PRE-AUTH VERIFICATION]
  │  Candidate enters Username & Email
  │  Uploads Document ID Photo + Live Selfie Photo
  │  AI Face Matcher evaluates facial similarity
  │  IF Match Confidence >= 90.0%:
  │      - Auto-generates 6-digit Password (e.g. 849201)
  │      - Sends Email Notification to candidate's email address
  ▼
[AUTHENTICATION & ONBOARDING WIZARD]
  │  Step 1: Log in with Username & Received Password
  │  Step 2: Accept Privacy Consent Agreement
  │  Step 3: Automated Browser System Check
  │  Step 4: Unlock Evaluation Session Dashboard
  ▼
[VIDEO FILE EVALUATION]
  │  AI Object Inference & Violation Interval Tracking
  │  Zero Tolerance Enforcement (Phone > 0s = FAILED)
  ▼
[EXAMINER DIRECTORY & REPORT INSPECTOR]
```

---
