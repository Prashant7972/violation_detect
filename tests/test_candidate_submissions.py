import os
import tempfile
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_test_video_clip(file_path: str, duration_sec: int = 2, fps: int = 30):
    height, width = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
    for i in range(duration_sec * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.ellipse(frame, (320, 240), (80, 110), 0, 0, 360, (140, 180, 210), -1)
        out.write(frame)
    out.release()

def test_candidate_multi_entry_submission_and_directory():
    temp_dir = tempfile.mkdtemp(prefix="test_cand_")
    video_path = os.path.join(temp_dir, "stu101_math_exam.mp4")

    try:
        create_test_video_clip(video_path, duration_sec=2, fps=30)
        assert os.path.exists(video_path)

        # 1. Post Video Entry with Student ID STU-1001
        with open(video_path, "rb") as vf:
            response = client.post(
                "/api/v1/videos/process?sample_fps=1.0&max_phone_limit=5.0",
                data={
                    "student_id": "STU-1001",
                    "student_name": "Alice Smith",
                    "exam_id": "MATH-101"
                },
                files={"file": ("stu101_math_exam.mp4", vf, "video/mp4")}
            )

        assert response.status_code == 200
        report = response.json()
        assert report["candidate_info"]["student_id"] == "STU-1001"
        assert report["candidate_info"]["student_name"] == "Alice Smith"

        # 2. Query Candidate Directory Search API
        dir_response = client.get("/api/v1/candidates?student_id=STU-1001")
        assert dir_response.status_code == 200
        dir_data = dir_response.json()
        assert dir_data["total_submissions"] >= 1
        assert dir_data["submissions"][0]["student_id"] == "STU-1001"

        # 3. Query Candidate Specific Endpoint
        cand_response = client.get("/api/v1/candidates/STU-1001")
        assert cand_response.status_code == 200
        cand_data = cand_response.json()
        assert len(cand_data["submissions"]) >= 1

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_credentials_lookup_and_login():
    # 1. Lookup credentials for candidate STU-DEMO (fallback demo)
    res = client.get("/api/v1/auth/credentials?username=STU-DEMO")
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "STU-DEMO"
    assert "password" in data
    assert data["status"] in ["ISSUED", "DEMO_FALLBACK"]

    # 2. Login with universal emergency/demo passcode ('123456' or 'proctor2026')
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "STU-DEMO", "password": "proctor2026"}
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["username"] == "STU-DEMO"
    assert login_data["status"] == "AUTHENTICATED"

    # 3. Also login with '123456'
    login_res2 = client.post(
        "/api/v1/auth/login",
        json={"username": "STU-DEMO", "password": "123456"}
    )
    assert login_res2.status_code == 200


def test_exam_submission_and_certificate():
    payload = {
        "student_id": "STU-TEST",
        "student_name": "Test Candidate",
        "exam_id": "MIDTERM-2026",
        "score": 5,
        "total_questions": 5,
        "answers": {"1": "A", "2": "A", "3": "A", "4": "A", "5": "A"},
        "face_match_percentage": "94.2%",
        "proctoring_status": "PASSED",
        "phone_violations": 0.0,
        "multiple_person_violations": 0.0
    }
    sub_res = client.post("/api/v1/exam/submit", json=payload)
    assert sub_res.status_code == 200
    data = sub_res.json()
    assert data["student_id"] == "STU-TEST"
    assert data["percentage"] == 100.0
    assert data["overall_status"] == "PASSED"
    assert data["certificate_id"].startswith("CERT-AI-")

    # Verify submission appears in candidate directory
    dir_res = client.get("/api/v1/candidates?student_id=STU-TEST")
    assert dir_res.status_code == 200
    dir_data = dir_res.json()
    assert dir_data["total_submissions"] >= 1
    found = any(s["student_id"] == "STU-TEST" for s in dir_data["submissions"])
    assert found is True


def test_live_scanner_and_student_evidence_storage():
    import base64
    from app.config import settings

    # 1. Test clean frame
    clean_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    # Draw simple face-like circle
    cv2.circle(clean_frame, (160, 120), 40, (200, 200, 200), -1)
    _, buffer = cv2.imencode('.jpg', clean_frame)
    b64_clean = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

    res_clean = client.post("/api/v1/sessions/scan-frame", json={
        "frame_data": b64_clean,
        "student_id": "STU-SCAN-99"
    })
    assert res_clean.status_code == 200
    data_clean = res_clean.json()
    assert "status" in data_clean
    assert "phone_detected" in data_clean
    assert "laptop_detected" in data_clean
    assert "multiple_persons" in data_clean

    # 2. Test candidate evidence query endpoint
    ev_res = client.get("/api/v1/candidates/STU-SCAN-99/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["student_id"] == "STU-SCAN-99"
    assert "evidence_frames" in ev_data
    assert isinstance(ev_data["evidence_frames"], list)


