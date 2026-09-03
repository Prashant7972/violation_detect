## 18. Detection Rules & Time Limits
| Rule ID | Event Type | Condition | Default Time Limit |
|---|---|---|---|
| `R-01` | `PHONE_DETECTED` | `IF object IN ['cell phone'] AND confidence >= 0.45` | **5.0 Seconds** |
| `R-02` | `MULTIPLE_PERSONS` | `IF count(person) > 1 AND confidence >= 0.65` | **3.0 Seconds** |
| `R-03` | `NO_PERSON_DETECTED` | `IF count(person) == 0 AND confidence >= 0.65` | **10.0 Seconds** |
| `R-04` | `UNAUTHORIZED_DEVICE` | `IF object IN ['laptop', 'tv'] AND confidence >= 0.70` | **5.0 Seconds** |

---
