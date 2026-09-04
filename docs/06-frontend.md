## 14. Serial Student ID Generation
When `student_id` is omitted or left blank:
1. System queries `CandidateSubmissionModel` for existing `student_id` records matching `STU-%`.
2. Extracts numeric suffixes, finds highest integer value ($N$).
3. Formats next ID as `STU-` + zero-padded integer ($N+1$).
4. Example sequence: `STU-001` $\rightarrow$ `STU-002` $\rightarrow$ `STU-003`.

---
