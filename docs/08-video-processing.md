## 16. Time Interval & Duration Tracking Workflow
- **Interval Creation**: When a rule violation starts on a sampled frame, a new interval object is created with `start_timestamp`.
- **Interval Extension**: If the violation continues on consecutive sampled frames, `end_timestamp` is updated.
- **Interval Close**: When the violation ceases, duration is calculated:
  $$\text{Duration} = (\text{End\_Time} - \text{Start\_Time}) + \frac{1.0}{\text{Sample\_FPS}}$$
- **Cumulative Duration**: Sum of all interval durations per event type across the video clip.

---
