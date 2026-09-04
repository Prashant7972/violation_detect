## 13. API Design & System Reset
### 1. System Reset API
- **HTTP Method**: `POST`
- **Path**: `/api/v1/system/reset`
- **Response Body (HTTP 200 OK)**:
```json
{
  "status": "SUCCESS",
  "message": "All database records and evidence files have been purged. Serial counter reset to STU-001.",
  "next_student_id": "STU-001"
}
```

### 2. Get Next Serial Student ID API
- **HTTP Method**: `GET`
- **Path**: `/api/v1/system/next-student-id`
- **Response Body (HTTP 200 OK)**:
```json
{
  "next_student_id": "STU-001"
}
```

### 3. Process Video Upload API
- **HTTP Method**: `POST`
- **Path**: `/api/v1/videos/process`
- **Request Form Data**: `file: UploadFile`, `student_id: Optional[str]`, `student_name: Optional[str]`, `exam_id: Optional[str]`
- **Response Body**: Full JSON analysis report.

---
