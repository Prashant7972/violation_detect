import os
import cv2
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional

from app.config import settings
from app.ai.detector import detector, AIDetector
from app.ai.rule_engine import RuleEngine

logger = logging.getLogger("app.ai.video_processor")

class VideoProcessor:
    """
    Processes video files, samples frames, runs AI detection & compliance rules,
    tracks simultaneous violation intervals, checks duration limits, and extracts
    multi-object color-coded evidence keyframes.
    """
    DEFAULT_LIMITS = {
        "PHONE_DETECTED": 5.0,           # Max 5.0 seconds allowed
        "NO_PERSON_DETECTED": 10.0,       # Max 10.0 seconds missing allowed
        "MULTIPLE_PERSONS": 3.0,          # Max 3.0 seconds multiple persons allowed
        "UNAUTHORIZED_DEVICE": 5.0        # Max 5.0 seconds unauthorized device allowed
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
    def process_video_file(
        cls,
        video_path: str,
        output_dir: str,
        sample_fps: float = 1.0,
        custom_limits: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Main video analysis entrypoint.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at path: {video_path}")

        limits = cls.DEFAULT_LIMITS.copy()
        if custom_limits:
            limits.update(custom_limits)

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

                    # Update or start active interval for this event type
                    if event_type not in active_intervals:
                        # Annotate frame with ALL detected violation objects (phones, persons, devices)
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
                        # Extend existing active interval
                        interval = active_intervals[event_type]
                        interval["end_time_sec"] = current_time_sec
                        interval["end_timestamp"] = formatted_time
                        interval["sample_count"] += 1
                        if rule["confidence"] > interval["peak_confidence"]:
                            interval["peak_confidence"] = rule["confidence"]

                # Close intervals for event types no longer present
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

        # Close any remaining active intervals at end of video
        for k, interval in active_intervals.items():
            interval_duration = (interval["end_time_sec"] - interval["start_time_sec"]) + (1.0 / sample_fps)
            interval["duration_seconds"] = round(interval_duration, 2)
            completed_intervals.append(interval)

        # Calculate cumulative durations per event type
        cumulative_durations: Dict[str, float] = {}
        for interval in completed_intervals:
            ev_type = interval["event_type"]
            cumulative_durations[ev_type] = round(
                cumulative_durations.get(ev_type, 0.0) + interval["duration_seconds"], 2
            )

        # Check limit thresholds
        limit_checks = {}
        overall_limit_exceeded = False

        for ev_type, duration in cumulative_durations.items():
            threshold = limits.get(ev_type, 10.0)
            exceeded = duration > threshold
            if exceeded:
                overall_limit_exceeded = True
            
            limit_checks[ev_type] = {
                "cumulative_duration_seconds": duration,
                "limit_threshold_seconds": threshold,
                "limit_exceeded": exceeded
            }

        # Build final analysis report
        report = {
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
            "overall_status": "FAILED" if overall_limit_exceeded else "PASSED",
            "overall_limit_exceeded": overall_limit_exceeded,
            "cumulative_durations": cumulative_durations,
            "limit_enforcement": limit_checks,
            "total_violation_intervals_count": len(completed_intervals),
            "violation_intervals": completed_intervals
        }

        # Save report JSON file
        report_json_path = os.path.join(output_dir, "analysis_report.json")
        with open(report_json_path, "w") as f:
            json.dump(report, f, indent=2)

        report["report_file_path"] = report_json_path
        return report
