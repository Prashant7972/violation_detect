## 15. Backend Workflow
1. API router accepts `UploadFile`.
2. Saves file to temporary path.
3. Calls `VideoProcessor`.
4. Returns report JSON and serves evidence keyframes under `/evidence/` endpoint.

---
