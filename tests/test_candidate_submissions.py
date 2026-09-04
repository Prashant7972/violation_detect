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
