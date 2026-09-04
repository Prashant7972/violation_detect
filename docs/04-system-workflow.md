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
