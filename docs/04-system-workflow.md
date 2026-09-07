## 7. Complete System Workflow
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Input Video │────►│ Serial ID    │────►│ AI Model     │────►│ Rule Engine  │
│ File (.mp4) │     │ Sampler      │     │ Inference    │     │ Evaluation   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Analysis    │◄────│ Evidence     │◄────│ Limit        │◄────│ Time         │
│ Report JSON │     │ Snapshotter  │     │ Enforcer     │     │ Intervalizer │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

---

## 37. Candidate Onboarding & Readiness Flow
### A. Stage-by-Stage Onboarding Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 1. ID Photo &   │────►│ 2. Login with   │────►│ 3. Privacy      │────►│ 4. Media & Sys  │────►│ 5. Session      │
│ Selfie Match    │     │ Username/Pass   │     │ Consent Check   │     │ Permissions     │     │ Launch & Video  │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Stage 1: Pre-Auth ID & Live Selfie Verification**:
   - Candidate enters Username and Email Address.
   - Candidate uploads Document ID Photo and takes a Live Selfie capture.
   - `FaceVerifier` calculates match confidence. If $\ge 90\%$, system generates password and sends email notification.
2. **Stage 2: Candidate Login**:
   - Candidate enters `Username` and `Password` received in their email.
3. **Stage 3: Consent & Privacy Agreement**:
   - Candidate accepts privacy terms.
4. **Stage 4: Media Permissions & System Environment Checks**:
   - Browser capability validation.
5. **Stage 5: Session Launch**:
   - System unlocks Candidate Video Processing Dashboard.

---

---

## 38. Passcode Generation & Ownership Architecture
Detail on Admin configured passcodes vs auto-generated candidate OTP passwords.

---

---

## 39. Pre-Auth Identity Verification & Email Password Dispatch Flow
### Facial Matching Confidence Enforcement ($\ge 75.0\%$)

```
┌─────────────────────────────────────────────────────────────┐
│ Candidate Document ID Photo vs Live Selfie Photo Comparison │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    Match Confidence Score (S)
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
    S >= 0.75 (75%)                       S < 0.75 (75%)
            │                                     │
            ▼                                     ▼
[MATCH SUCCESS (VERIFIED)]             [MATCH FAILED (REJECTED)]
- Auto-generate Password                - HTTP 400 Bad Request
- Dispatch Email Notification           - Error: "Match confidence (68.2%)
- Unlock Login Step                       is below required 75% threshold."
```
