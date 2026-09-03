## 6. User Workflow
```
USER
  │
  ├─► Provides Video Clip Input (e.g. video.mp4)
  │
  ├─► Configures Sampling FPS (e.g. 1 FPS) & Duration Limits
  │
  ├─► Executes CLI script `python process_video.py --input video.mp4`
  │   OR uploads file via API `POST /api/v1/videos/process`
  │
  ├─► System processes video clip frame-by-frame
  │
  ├─► System calculates violation time intervals & cumulative durations
  │
  ├─► System extracts annotated evidence keyframe images
  │
  └─► Receives structured JSON Analysis Report & Evidence directory
```

---
