## 14. Video File Processing Workflow
1. `VideoProcessor.process_video_file()` opens input video file with `cv2.VideoCapture`.
2. Extracts native FPS and total frames to compute video duration.
3. Steps through frames using `frame_idx % frame_step == 0`.
4. Decodes image array and calculates current video timestamp (`HH:MM:SS.mmm`).
5. Passes frame to `AIDetector.detect()` and `RuleEngine.evaluate()`.

---
