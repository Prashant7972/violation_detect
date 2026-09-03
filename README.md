# Real-Time AI Visual Detection & Event Monitoring System

A complete local solution for real-time video frame capture, AI object detection, automated compliance rule evaluation, and visual evidence logging.

---

## Features
- **WebRTC Camera Sampling**: Captures webcam stream from HTML5 canvas at 1 - 5 FPS.
- **FastAPI Async Pipeline**: High-throughput REST API for frame payload validation.
- **OpenCV & AI Object Detector**: Decodes image frames and runs object detection (YOLOv8 / OpenCV Haar Cascades).
- **Rule Engine**: Flags security violations (`PHONE_DETECTED`, `MULTIPLE_PERSONS`, `NO_PERSON_DETECTED`, `UNAUTHORIZED_DEVICE`).
- **Visual Evidence Generator**: Highlights bounding boxes and stores annotated JPEG evidence snapshots to disk and SQLite database.
- **Real-Time Dashboard**: Web interface displaying live camera feed, active session metrics, and real-time alert logs.
- **36-Section Master Documentation**: Complete project reference guide covering local setup through future cloud production scaling.

---

## Quick Start (Local Setup)

### 1. Install Dependencies
```bash
cd /home/prashant/.gemini/antigravity/scratch/ai_detection_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Application Server
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open Web Dashboard
Navigate your browser to:
[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

### 4. Interactive API Documentation
Open Swagger UI at:
[http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure
- `PROJECT_DOCUMENTATION.md` - Complete 36-section master project reference.
- `docs/` - Modular documentation broken down by topic.
- `app/main.py` - FastAPI application entrypoint.
- `app/api/` - REST API endpoints and Pydantic schemas.
- `app/db/` - SQLAlchemy models (`Session`, `Event`, `Evidence`).
- `app/ai/` - Detector adapter and rule engine logic.
- `app/static/` - Web frontend client (HTML, CSS, JS).
- `evidence/` - Generated visual evidence snapshots.
- `tests/` - Pytest automated test suite.
# Prashant-demo-project

#testing
