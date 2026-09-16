"""
Dynamic Conditional Edge Routers for LangGraph Proctor Orchestrator
"""

import logging
from src.core.state import ProctorSessionState

logger = logging.getLogger("orchestrator_router")


def route_decision(state: ProctorSessionState) -> str:
    """
    Conditional edge router evaluating the orchestrator decision.
    Routes to human-in-the-loop triage if candidate violation severity
    or risk points require human proctor intervention.
    """
    decision = state.get("orchestrator_decision", "CONTINUE")
    
    if decision in ["ESCALATE_HUMAN", "TERMINATE"]:
        logger.info(f"Decision '{decision}' routed to human_review_interrupt.")
        return "human_review_interrupt"
    
    return "state_persistence"
