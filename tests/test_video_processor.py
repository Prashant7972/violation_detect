import os
import tempfile
import cv2
import numpy as np
import pytest
from app.ai.video_processor import VideoProcessor

def create_synthetic_test_video(file_path: str, duration_sec: int = 5, fps: int = 30):
    """Generates a synthetic test video clip with a blue circle."""
    height, width = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw candidate representation (skin tone circle)
        cv2.ellipse(frame, (320, 240), (80, 110), 0, 0, 360, (140, 180, 210), -1)
        out.write(frame)

    out.release()

def test_video_processor_analysis():
    temp_dir = tempfile.mkdtemp(prefix="test_vid_proc_")
    video_path = os.path.join(temp_dir, "sample_clip.mp4")
    output_dir = os.path.join(temp_dir, "analysis_output")

    try:
        create_synthetic_test_video(video_path, duration_sec=4, fps=30)
        assert os.path.exists(video_path)

        report = VideoProcessor.process_video_file(
            video_path=video_path,
            output_dir=output_dir,
            sample_fps=1.0,
            custom_limits={"PHONE_DETECTED": 2.0, "NO_PERSON_DETECTED": 5.0}
        )

        assert report["video_file"] == "sample_clip.mp4"
        assert report["video_metadata"]["duration_seconds"] == 4.0
        assert "overall_status" in report
        assert "cumulative_durations" in report
        assert "limit_enforcement" in report
        assert os.path.exists(report["report_file_path"])

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_video_processor_evidence_saving_per_student():
    """Verifies that keyframe evidence images are physically saved on disk per student_id."""
    temp_dir = tempfile.mkdtemp(prefix="test_ev_disk_")
    video_path = os.path.join(temp_dir, "violation_clip.mp4")

    try:
        height, width = 480, 640
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 10, (width, height))

        # Blank frames (will trigger NO_PERSON_DETECTED rule and create evidence keyframe)
        for _ in range(30):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            out.write(frame)
        out.release()

        report = VideoProcessor.process_video_file(
            video_path=video_path,
            output_dir=None,
            sample_fps=2.0,
            custom_limits={"NO_PERSON_DETECTED": 1.0},
            student_id="STU-VERIFY-007",
            student_name="James Bond",
            exam_id="AI-PROCTOR-FINAL"
        )

        assert report["overall_status"] == "FAILED"
        assert len(report["evidence_frames"]) > 0

        ev_item = report["evidence_frames"][0]
        assert ev_item["student_id"] == "STU-VERIFY-007"
        assert "evidence_url" in ev_item
        assert "evidence_file" in ev_item
        assert os.path.exists(ev_item["evidence_file"]), f"Evidence file was not saved to disk: {ev_item['evidence_file']}"
        assert "STU-VERIFY-007" in ev_item["evidence_file"]

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

