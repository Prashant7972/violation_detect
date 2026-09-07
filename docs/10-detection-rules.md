## 18. Detection Rules & Time Limits
| Rule ID | Event Code | Condition | Default Limit |
|---|---|---|---|
| `R-01` | `PHONE_DETECTED` | `IF object IN ['cell phone'] AND confidence >= 0.30` | **0.0 Seconds (Zero Tolerance)** |
| `R-02` | `MULTIPLE_PERSONS` | `IF count(person) > 1 AND confidence >= 0.55` | **0.0 Seconds (Zero Tolerance)** |
| `R-03` | `NO_PERSON_DETECTED` | `IF count(person) == 0 AND confidence >= 0.55` | **5.0 Seconds** |

---
