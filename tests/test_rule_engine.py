import pytest
from app.ai.rule_engine import RuleEngine

def test_phone_detection_rule():
    detections = [
        {"object": "cell phone", "confidence": 0.88, "bounding_box": [10, 10, 50, 100]},
        {"object": "person", "confidence": 0.95, "bounding_box": [0, 0, 200, 300]}
    ]
    events = RuleEngine.evaluate(detections)
    assert len(events) == 1
    assert events[0]["event_type"] == "PHONE_DETECTED"
    assert events[0]["confidence"] == 0.88

def test_multiple_persons_rule():
    detections = [
        {"object": "person", "confidence": 0.90, "bounding_box": [0, 0, 100, 200]},
        {"object": "person", "confidence": 0.85, "bounding_box": [120, 0, 220, 200]}
    ]
    events = RuleEngine.evaluate(detections)
    assert any(e["event_type"] == "MULTIPLE_PERSONS" for e in events)

def test_no_person_detected_rule():
    detections = []
    events = RuleEngine.evaluate(detections)
    assert len(events) == 1
    assert events[0]["event_type"] == "NO_PERSON_DETECTED"

def test_clean_single_person_frame():
    detections = [
        {"object": "person", "confidence": 0.92, "bounding_box": [10, 10, 300, 400]}
    ]
    events = RuleEngine.evaluate(detections)
    assert len(events) == 0
