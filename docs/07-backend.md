## 15. Backend Workflow
1. Client calls `POST /api/v1/videos/process`.
2. Serial generator resolves `student_id`.
3. `VideoProcessor` executes frame sampling & rule evaluations.
4. Saves DB record and outputs JSON report.

---
