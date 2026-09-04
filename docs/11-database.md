## 12. Database Design
### `candidate_submissions` Table
| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Record ID |
| `submission_id` | VARCHAR(64) | UNIQUE INDEX | Unique submission UUID |
| `student_id` | VARCHAR(64) | NOT NULL INDEX | Serial Student ID (e.g. `STU-001`) |
| `student_name` | VARCHAR(128) | NULLABLE | Candidate Full Name |
| `exam_id` | VARCHAR(64) | NULLABLE INDEX | Exam Identifier |
| `video_filename` | VARCHAR(256) | NOT NULL | Input Video Filename |
| `video_duration_seconds` | FLOAT | NOT NULL | Total Video Length (sec) |
| `overall_status` | VARCHAR(32) | NOT NULL | `PASSED` or `FAILED` |
| `phone_duration_seconds` | FLOAT | DEFAULT 0.0 | Total Phone Usage Time |
| `missing_duration_seconds` | FLOAT | DEFAULT 0.0 | Total Candidate Missing Time |
| `report_json_path` | VARCHAR(512) | NOT NULL | Report File Path |
| `evidence_dir_path` | VARCHAR(512) | NOT NULL | Evidence Folder Path |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Submission Timestamp |

---
