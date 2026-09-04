import os
import cv2
import json
import logging
import time
import re
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.config import settings
from app.ai.detector import detector, AIDetector
from app.ai.rule_engine import RuleEngine
from app.db.models import CandidateSubmissionModel

logger = logging.getLogger("app.ai.video_processor")

class VideoProcessor:
    """
    Processes video files, samples frames, runs AI detection & compliance rules,
    tracks simultaneous violation intervals, checks duration limits, extracts
    multi-object evidence keyframes, and persists Candidate/Student submission records.
    """
    DEFAULT_LIMITS = {
        "PHONE_DETECTED": 0.0,           # Zero tolerance (any phone usage causes FAILED)
        "MULTIPLE_PERSONS": 0.0,         # Zero tolerance (any second person causes FAILED)
        "UNAUTHORIZED_DEVICE": 0.0,      # Zero tolerance (any laptop/TV causes FAILED)
        "NO_PERSON_DETECTED": 5.0        # Max 5.0 seconds missing allowed
    }

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Formats seconds float into HH:MM:SS.mmm string."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        if millis >= 1000:
            secs += 1
            millis = 0
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

    @classmethod
    def get_next_serial_student_id(cls, db_session: Optional[Any] = None) -> str:
        """
        Generates the next sequential, zero-padded Student ID (STU-001, STU-002, STU-003, ...).
        """
        if db_session is None:
            return "STU-001"

        try:
            submissions = db_session.query(CandidateSubmissionModel.student_id).filter(
                CandidateSubmissionModel.student_id.like("STU-%")
            ).all()

            numbers = []
            for (s_id,) in submissions:
                match = re.search(r"STU-(\d+)", s_id, re.IGNORECASE)
                if match:
                    numbers.append(int(match.group(1)))

            next_num = max(numbers) + 1 if numbers else 1
            return f"STU-{next_num:03d}"
        except Exception as e:
            logger.error(f"Error calculating next serial student ID: {e}")
            return "STU-001"

    @classmethod
    def process_video_file(
        cls,
        video_path: str,
        output_dir: Optional[str] = None,
        sample_fps: float = 1.0,
        custom_limits: Optional[Dict[str, float]] = None,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        exam_id: Optional[str] = None,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Main video analysis entrypoint for Candidate/Student submissions.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at path: {video_path}")

        # Generate serial Student ID if student_id is empty, generic, or omitted
        if not student_id or student_id.strip() in ["", "STU-UNKNOWN", "STU-101"]:
            student_id = cls.get_next_serial_student_id(db_session)
        else:
            student_id = student_id.strip()

        limits = cls.DEFAULT_LIMITS.copy()
        if custom_limits:
            limits.update(custom_limits)

        # Candidate-isolated storage path
        clean_file_stem = os.path.splitext(os.path.basename(video_path))[0]
        timestamp_slug = int(time.time() * 1000)
        
        if not output_dir:
            output_dir = os.path.join(settings.EVIDENCE_DIR, "candidates", student_id, f"{clean_file_stem}_{timestamp_slug}")

        os.makedirs(output_dir, exist_ok=True)
        evidence_dir = os.path.join(output_dir, "extracted_evidence")
        os.makedirs(evidence_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        native_fps = cap.get(cv2.CAP_PROP_FPS)
        if native_fps <= 0 or np.isnan(native_fps):
            native_fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration_sec = total_frames / native_fps if native_fps > 0 else 0.0

        frame_step = max(1, int(native_fps / sample_fps))

        frame_idx = 0
        active_intervals: Dict[str, Dict[str, Any]] = {}
        completed_intervals: List[Dict[str, Any]] = []

        raw_frame_results = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                current_time_sec = frame_idx / native_fps
                formatted_time = cls.format_timestamp(current_time_sec)

                # AI Inference & Rule Evaluation
                detection_res = detector.detect(frame)
                detections = detection_res.get("detections", [])
                triggered_rules = RuleEngine.evaluate(detections)

                rule_types_present = set()

                for rule in triggered_rules:
                    event_type = rule["event_type"]
                    rule_types_present.add(event_type)

                    if event_type not in active_intervals:
                        annotated = AIDetector.annotate_frame(frame, detections)
                        
                        kf_name = f"evidence_{event_type.lower()}_{int(current_time_sec*1000)}ms.jpg"
                        kf_path = os.path.join(evidence_dir, kf_name)
                        cv2.imwrite(kf_path, annotated)

                        active_intervals[event_type] = {
                            "event_type": event_type,
                            "rule_triggered": rule["rule_triggered"],
                            "start_time_sec": current_time_sec,
                            "end_time_sec": current_time_sec,
                            "start_timestamp": formatted_time,
                            "end_timestamp": formatted_time,
                            "peak_confidence": rule["confidence"],
                            "evidence_file": kf_path,
                            "sample_count": 1
                        }
                    else:
                        interval = active_intervals[event_type]
                        interval["end_time_sec"] = current_time_sec
                        interval["end_timestamp"] = formatted_time
                        interval["sample_count"] += 1
                        if rule["confidence"] > interval["peak_confidence"]:
                            interval["peak_confidence"] = rule["confidence"]

                ended_keys = [k for k in active_intervals if k not in rule_types_present]
                for k in ended_keys:
                    interval = active_intervals.pop(k)
                    interval_duration = (interval["end_time_sec"] - interval["start_time_sec"]) + (1.0 / sample_fps)
                    interval["duration_seconds"] = round(interval_duration, 2)
                    completed_intervals.append(interval)

                raw_frame_results.append({
                    "frame_index": frame_idx,
                    "timestamp_sec": round(current_time_sec, 2),
                    "formatted_timestamp": formatted_time,
                    "detections": detections,
                    "events": [r["event_type"] for r in triggered_rules]
                })

            frame_idx += 1

        cap.release()

        for k, interval in active_intervals.items():
            interval_duration = (interval["end_time_sec"] - interval["start_time_sec"]) + (1.0 / sample_fps)
            interval["duration_seconds"] = round(interval_duration, 2)
            completed_intervals.append(interval)

        # Calculate cumulative durations
        cumulative_durations: Dict[str, float] = {}
        for interval in completed_intervals:
            ev_type = interval["event_type"]
            cumulative_durations[ev_type] = round(
                cumulative_durations.get(ev_type, 0.0) + interval["duration_seconds"], 2
            )

        limit_checks = {}
        overall_limit_exceeded = False

        for ev_type, duration in cumulative_durations.items():
            threshold = limits.get(ev_type, 0.0)
            exceeded = (duration > threshold) if threshold > 0 else (duration > 0)
            if exceeded:
                overall_limit_exceeded = True
            
            limit_checks[ev_type] = {
                "cumulative_duration_seconds": duration,
                "limit_threshold_seconds": threshold,
                "limit_exceeded": exceeded
            }

        overall_status = "FAILED" if overall_limit_exceeded else "PASSED"

        # Build report structure
        report = {
            "candidate_info": {
                "student_id": student_id,
                "student_name": student_name or student_id,
                "exam_id": exam_id or "GENERAL"
            },
            "video_file": os.path.basename(video_path),
            "video_metadata": {
                "native_fps": round(native_fps, 2),
                "total_frames": total_frames,
                "duration_seconds": round(video_duration_sec, 2),
                "duration_formatted": cls.format_timestamp(video_duration_sec)
            },
            "analysis_settings": {
                "sample_fps": sample_fps,
                "sampled_frames_processed": len(raw_frame_results),
                "limits_configured": limits
            },
            "overall_status": overall_status,
            "overall_limit_exceeded": overall_limit_exceeded,
            "cumulative_durations": cumulative_durations,
            "limit_enforcement": limit_checks,
            "total_violation_intervals_count": len(completed_intervals),
            "violation_intervals": completed_intervals
        }

        report_json_path = os.path.join(output_dir, "analysis_report.json")
        with open(report_json_path, "w") as f:
            json.dump(report, f, indent=2)

        report["report_file_path"] = report_json_path

        # Persist DB record if db_session is provided
        if db_session is not None:
            submission_obj = CandidateSubmissionModel(
                student_id=student_id,
                student_name=student_name,
                exam_id=exam_id,
                video_filename=os.path.basename(video_path),
                video_duration_seconds=round(video_duration_sec, 2),
                overall_status=overall_status,
                limit_exceeded=1 if overall_limit_exceeded else 0,
                phone_duration_seconds=cumulative_durations.get("PHONE_DETECTED", 0.0),
                missing_duration_seconds=cumulative_durations.get("NO_PERSON_DETECTED", 0.0),
                multiple_persons_duration_seconds=cumulative_durations.get("MULTIPLE_PERSONS", 0.0),
                report_json_path=report_json_path,
                evidence_dir_path=output_dir
            )
            db_session.add(submission_obj)
            db_session.commit()
            db_session.refresh(submission_obj)
            report["submission_id"] = submission_obj.submission_id
            report["db_id"] = submission_obj.id

        return report
