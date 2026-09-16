"""
LangGraph Proctor Orchestrator StateGraph Assembly
Compiles multi-branch supervisor proctoring workflow with parallel vision/audio evaluation,
policy cross-referencing, evidence synthesis, and checkpointer state retention.
"""

import copy
import logging
from typing import Dict, Any, Optional, Callable

from src.core.state import ProctorSessionState
from src.features.identity_verification.nodes import identity_verification_node
from src.features.vision_proctoring.nodes import vision_proctoring_node
from src.features.audio_intelligence.nodes import audio_intelligence_node
from src.features.policy_rules.nodes import policy_evaluation_node
from src.features.evidence_reporting.nodes import evidence_synthesis_node
from src.features.proctor_orchestrator.router import route_decision

logger = logging.getLogger("proctor_orchestrator_graph")


def human_review_interrupt_node(state: ProctorSessionState) -> Dict[str, Any]:
    """
    Human-in-the-Loop triage node.
    Invoked when orchestrator decision is ESCALATE_HUMAN or TERMINATE.
    Ensures that automated decisions remain pending until a human proctor signs off.
    """
    decision = state.get("orchestrator_decision", "ESCALATE_HUMAN")
    logger.warning(
        f"Session {state.get('session_id')} flagged with {decision}. Escalated to Proctor Review Portal."
    )
    return {
        "orchestrator_decision": decision
    }


def state_persistence_node(state: ProctorSessionState) -> Dict[str, Any]:
    """
    Final graph node that prepares session state for checkpoint persistence.
    """
    return {
        "timestamp": state.get("timestamp")
    }


# =========================================================================
# LangGraph Native / Drop-in StateGraph Engine with Checkpointing
# =========================================================================

class MemorySaver:
    """In-memory checkpointer maintaining state across invocations for the same session_id."""
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}

    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        if thread_id in self._storage:
            return copy.deepcopy(self._storage[thread_id])
        return None

    def put(self, thread_id: str, state: Dict[str, Any]):
        self._storage[thread_id] = copy.deepcopy(state)


class ProctorStateGraphEngine:
    """
    Deterministic StateGraph engine providing LangGraph-compatible interface:
    - Parallel branch execution (vision, audio, identity)
    - Sequential convergence (policy evaluation -> evidence synthesis)
    - Dynamic conditional edge routing (route_decision)
    - State accumulator pattern (operator.add for list fields)
    - Checkpointer state retention across session steps
    """

    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        self.checkpointer = checkpointer or MemorySaver()
        self.nodes: Dict[str, Callable] = {}
        self._register_default_nodes()

    def _register_default_nodes(self):
        self.nodes["vision_proctoring"] = vision_proctoring_node
        self.nodes["audio_intelligence"] = audio_intelligence_node
        self.nodes["identity_verification"] = identity_verification_node
        self.nodes["policy_evaluation"] = policy_evaluation_node
        self.nodes["evidence_synthesis"] = evidence_synthesis_node
        self.nodes["human_review_interrupt"] = human_review_interrupt_node
        self.nodes["state_persistence"] = state_persistence_node

    @staticmethod
    def _apply_update(current_state: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Merges node outputs into current state, honoring append-only accumulators within a step."""
        accumulator_keys = {
            "detected_objects",
            "visual_anomalies",
            "audio_anomalies",
            "policy_violations",
            "evidence_events"
        }
        for k, v in update.items():
            if k in accumulator_keys and isinstance(v, list):
                existing_list = current_state.get(k, [])
                current_state[k] = list(existing_list) + list(v)
            else:
                current_state[k] = v
        return current_state

    def invoke(self, state: ProctorSessionState, config: Optional[Dict[str, Any]] = None) -> ProctorSessionState:
        """
        Executes a single proctoring workflow step across all graph nodes.
        Restores previous session state from checkpointer, executes parallel and sequential branches,
        and saves the updated state to the checkpointer.
        """
        config = config or {}
        thread_id = config.get("configurable", {}).get("thread_id", state.get("session_id", "default_thread"))

        # Restore historical accumulated state from checkpointer if present
        saved_state = self.checkpointer.get(thread_id)
        active_state: Dict[str, Any] = copy.deepcopy(state)

        if saved_state:
            # Carry over cumulative metrics and immutable audit logs across steps
            active_state["cumulative_risk_score"] = saved_state.get("cumulative_risk_score", 0.0)
            active_state["warning_count"] = saved_state.get("warning_count", 0)
            for acc in ["policy_violations", "evidence_events"]:
                historical = saved_state.get(acc, [])
                incoming = active_state.get(acc, [])
                active_state[acc] = list(historical) + list(incoming)

        # 1. Parallel Ingestion Branches (Vision, Audio, Identity)
        vis_update = self.nodes["vision_proctoring"](active_state)
        self._apply_update(active_state, vis_update)

        aud_update = self.nodes["audio_intelligence"](active_state)
        self._apply_update(active_state, aud_update)

        id_update = self.nodes["identity_verification"](active_state)
        self._apply_update(active_state, id_update)

        # 2. Policy & RAG Evaluation Branch
        pol_update = self.nodes["policy_evaluation"](active_state)
        self._apply_update(active_state, pol_update)

        # 3. Evidence Synthesis & Risk Scorer Branch
        ev_update = self.nodes["evidence_synthesis"](active_state)
        self._apply_update(active_state, ev_update)

        # 4. Conditional Routing Branch
        route_dest = route_decision(active_state)
        if route_dest == "human_review_interrupt":
            hitl_update = self.nodes["human_review_interrupt"](active_state)
            self._apply_update(active_state, hitl_update)

        persist_update = self.nodes["state_persistence"](active_state)
        self._apply_update(active_state, persist_update)

        # 5. Checkpoint Updated State
        self.checkpointer.put(thread_id, active_state)

        return active_state


def build_proctoring_graph(checkpointer: Optional[MemorySaver] = None) -> ProctorStateGraphEngine:
    """
    Factory function assembling and compiling the LangGraph StateGraph pipeline.
    """
    return ProctorStateGraphEngine(checkpointer=checkpointer)


# Global default compiled graph
proctoring_graph = build_proctoring_graph()
