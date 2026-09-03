## 13. API Design
### Process Video Upload
- **HTTP Method**: `POST`
- **Path**: `/api/v1/videos/process`
- **Request**: Multipart Form Data (`file: UploadFile`, `sample_fps: float`, `max_phone_limit: float`)
- **Response Body (HTTP 200 OK)**:
```json
{
  "video_file": "candidate_exam.mp4",
  "video_metadata": {
    "native_fps": 30.0,
    "total_frames": 3600,
    "duration_seconds": 120.0,
    "duration_formatted": "00:02:00.000"
  },
  "overall_status": "FAILED",
  "overall_limit_exceeded": true,
  "cumulative_durations": {
    "PHONE_DETECTED": 14.5,
    "NO_PERSON_DETECTED": 2.0
  },
  "limit_enforcement": {
    "PHONE_DETECTED": {
      "cumulative_duration_seconds": 14.5,
      "limit_threshold_seconds": 5.0,
      "limit_exceeded": true
    }
  },
  "violation_intervals": [
    {
      "event_type": "PHONE_DETECTED",
      "rule_triggered": "IF object IN ['cell phone'] AND confidence >= 0.45",
      "start_timestamp": "00:00:12.000",
      "end_timestamp": "00:00:26.500",
      "duration_seconds": 14.5,
      "peak_confidence": 0.91,
      "evidence_file": "/evidence/video_candidate_exam/evidence_phone_detected_12000ms.jpg"
    }
  ]
}
```

---
