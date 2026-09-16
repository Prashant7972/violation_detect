"""
Evidence Timeline Builder
Constructs immutable, chronological audit trails and explainable violation summaries.
"""

from typing import List, Dict, Any
from datetime import datetime

from src.features.evidence_reporting.schemas import EvidenceEvent
from src.features.vision_proctoring.schemas import AnomalySeverity


class EvidenceTimelineBuilder:
    """
    Builds structured, chronological proctoring audit trails for proctors and academic committees.
    """

    @staticmethod
    def build_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sorts and formats evidence events in chronological order."""
        if not events:
            return []

        def parse_ts(ev):
            ts = ev.get("timestamp", "")
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                return datetime.min

        return sorted(events, key=parse_ts)

    @staticmethod
    def generate_session_summary(
        session_id: str,
        candidate_id: str,
        cumulative_risk: float,
        warning_count: int,
        decision: str,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generates comprehensive metrics summary for the proctor review portal."""
        severity_counts = {
            AnomalySeverity.CRITICAL.value: 0,
            AnomalySeverity.HIGH.value: 0,
            AnomalySeverity.MEDIUM.value: 0,
            AnomalySeverity.LOW.value: 0
        }

        for ev in events:
            sev = ev.get("severity", "LOW")
            if sev in severity_counts:
                severity_counts[sev] += 1

        pending_reviews = sum(
            1 for ev in events if ev.get("proctor_review_status") == "PENDING_VERIFICATION"
        )

        return {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "cumulative_risk_score": round(min(100.0, max(0.0, cumulative_risk)), 1),
            "warning_count": warning_count,
            "current_decision": decision,
            "total_evidence_events": len(events),
            "pending_proctor_reviews": pending_reviews,
            "severity_breakdown": severity_counts,
            "requires_immediate_human_triage": decision in ["ESCALATE_HUMAN", "TERMINATE"]
        }


# Global timeline builder instance
timeline_builder = EvidenceTimelineBuilder()
