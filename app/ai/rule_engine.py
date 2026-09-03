from typing import List, Dict, Any
from app.config import settings

class RuleEngine:
    """
    Evaluates raw AI object detection arrays against configured compliance rules.
    Allows simultaneous multi-rule detection on the same video frame.
    """
    @staticmethod
    def evaluate(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates detection items and returns a list of triggered event objects:
        [
            {
                "event_type": "PHONE_DETECTED",
                "rule_triggered": "Cell phone detected in video frame",
                "confidence": 0.88,
                "flagged_detections": [...]
            }
        ]
        """
        events = []

        phones = [
            d for d in detections 
            if d.get("object") in ["cell phone", "phone", "mobile", "remote", "telephone"] 
            and d.get("confidence", 0.0) >= settings.PHONE_CONFIDENCE_THRESHOLD
        ]
        persons = [
            d for d in detections 
            if d.get("object") == "person" 
            and d.get("confidence", 0.0) >= settings.PERSON_CONFIDENCE_THRESHOLD
        ]
        devices = [
            d for d in detections 
            if d.get("object") in ["laptop", "tv", "keyboard"] 
            and d.get("confidence", 0.0) >= 0.65
        ]

        # Rule 1: Cell Phone Detection
        if phones:
            max_conf = max(p["confidence"] for p in phones)
            events.append({
                "event_type": "PHONE_DETECTED",
                "rule_triggered": f"IF object IN ['cell phone'] AND confidence >= {settings.PHONE_CONFIDENCE_THRESHOLD}",
                "confidence": max_conf,
                "flagged_detections": phones
            })

        # Rule 2: Multiple Persons Detection
        if len(persons) > 1:
            max_conf = max(p["confidence"] for p in persons)
            events.append({
                "event_type": "MULTIPLE_PERSONS",
                "rule_triggered": f"IF count(person) > 1 AND confidence >= {settings.PERSON_CONFIDENCE_THRESHOLD}",
                "confidence": max_conf,
                "flagged_detections": persons
            })

        # Rule 3: Candidate Missing / No Person
        elif len(persons) == 0:
            events.append({
                "event_type": "NO_PERSON_DETECTED",
                "rule_triggered": f"IF count(person) == 0 AND confidence >= {settings.PERSON_CONFIDENCE_THRESHOLD}",
                "confidence": 1.0,
                "flagged_detections": []
            })

        # Rule 4: Unauthorized Secondary Electronic Device (Laptops / TVs)
        if devices:
            max_conf = max(d["confidence"] for d in devices)
            events.append({
                "event_type": "UNAUTHORIZED_DEVICE",
                "rule_triggered": "IF object IN ['laptop', 'tv'] AND confidence >= 0.65",
                "confidence": max_conf,
                "flagged_detections": devices
            })

        return events
