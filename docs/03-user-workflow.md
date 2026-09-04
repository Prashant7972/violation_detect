## 6. User Workflow
```
USER / ADMIN
  │
  ├─► Provides Video Clip Input (e.g. candidate_video.mp4)
  │
  ├─► Leaves Student ID blank or provides custom Student ID (e.g. STU-001)
  │
  ├─► Submits video file via CLI `python process_video.py` or Web UI Dashboard
  │
  ├─► System processes video clip & calculates violation time intervals
  │
  ├─► System stores evidence in candidate-isolated directory `/evidence/candidates/STU-001/`
  │
  └─► Admin can view Candidate Directory or click "Reset All Data" to start clean
```

---
