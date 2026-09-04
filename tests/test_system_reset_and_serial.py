import os
import tempfile
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_test_clip(file_path: str, duration_sec: int = 1, fps: int = 30):
    height, width = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
    for i in range(duration_sec * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.ellipse(frame, (320, 240), (80, 110), 0, 0, 360, (140, 180, 210), -1)
        out.write(frame)
    out.release()

def test_system_reset_and_serial_student_ids():
    temp_dir = tempfile.mkdtemp(prefix="test_reset_")
    video_path_1 = os.path.join(temp_dir, "clip1.mp4")
    video_path_2 = os.path.join(temp_dir, "clip2.mp4")

    try:
        create_test_clip(video_path_1)
        create_test_clip(video_path_2)

        # 1. Reset system to get clean state
        reset_res = client.post("/api/v1/system/reset")
        assert reset_res.status_code == 200
        assert reset_res.json()["next_student_id"] == "STU-001"

        # 2. Query next serial Student ID
        next_res = client.get("/api/v1/system/next-student-id")
        assert next_res.status_code == 200
        assert next_res.json()["next_student_id"] == "STU-001"

        # 3. Submit first video with empty student_id -> auto-assigned STU-001
        with open(video_path_1, "rb") as vf1:
            sub1 = client.post(
                "/api/v1/videos/process?sample_fps=1.0",
                data={"student_id": ""},
                files={"file": ("clip1.mp4", vf1, "video/mp4")}
            )
        assert sub1.status_code == 200
        r1 = sub1.json()
        assert r1["candidate_info"]["student_id"] == "STU-001"

        # 4. Query next serial Student ID -> should be STU-002
        next_res2 = client.get("/api/v1/system/next-student-id")
        assert next_res2.json()["next_student_id"] == "STU-002"

        # 5. Submit second video with empty student_id -> auto-assigned STU-002
        with open(video_path_2, "rb") as vf2:
            sub2 = client.post(
                "/api/v1/videos/process?sample_fps=1.0",
                data={"student_id": ""},
                files={"file": ("clip2.mp4", vf2, "video/mp4")}
            )
        assert sub2.status_code == 200
        r2 = sub2.json()
        assert r2["candidate_info"]["student_id"] == "STU-002"

        # 6. Perform System Reset
        reset_res2 = client.post("/api/v1/system/reset")
        assert reset_res2.status_code == 200
        assert reset_res2.json()["status"] == "SUCCESS"

        # 7. Verify Candidate Directory is empty after reset
        dir_res = client.get("/api/v1/candidates")
        assert dir_res.status_code == 200
        assert dir_res.json()["total_submissions"] == 0

        # 8. Verify next Student ID is reset back to STU-001
        next_res3 = client.get("/api/v1/system/next-student-id")
        assert next_res3.json()["next_student_id"] == "STU-001"

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
