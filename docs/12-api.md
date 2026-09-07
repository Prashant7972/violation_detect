## 13. API Design & System Reset
### 1. Pre-Auth Identity Verification API
- **HTTP Method**: `POST`
- **Path**: `/api/v1/onboarding/verify-id`
- **Request Body**: `{"username": "STU-001", "email": "candidate@example.com", "document_id_b64": "...", "live_selfie_b64": "..."}`
- **Response**: `{"status": "VERIFIED", "match_confidence": 0.945, "match_percentage": "94.5%", "email_sent_to": "candidate@example.com"}`

### 2. Candidate Login API
- **HTTP Method**: `POST`
- **Path**: `/api/v1/auth/login`
- **Request Body**: `{"username": "STU-001", "password": "849201"}`
- **Response**: `{"access_token": "tok-STU-001-a1b2c3d4", "status": "AUTHENTICATED"}`

---
