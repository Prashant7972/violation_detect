"""
Policy Retrieval Engine with ChromaDB Vector Support and JSON Fallback
Retrieves examination rules, institutional overrides, and prohibited hardware catalogs.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Set

from src.features.policy_rules.schemas import AnomalySeverity

logger = logging.getLogger("policy_retriever")

DEFAULT_POLICY_PATH = os.path.join(os.path.dirname(__file__), "policy_store.json")


class PolicyRetriever:
    """
    RAG-backed policy retrieval engine.
    Cross-references institutional guidelines against candidate observations.
    """

    def __init__(self, policy_file_path: Optional[str] = None):
        self.policy_file_path = policy_file_path or DEFAULT_POLICY_PATH
        self._policy_data = self._load_default_policy()
        self._chroma_collection = None
        self._initialize_chroma()

    def _load_default_policy(self) -> Dict[str, Any]:
        """Loads baseline test rules and allowances from policy_store.json."""
        try:
            if os.path.exists(self.policy_file_path):
                with open(self.policy_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading policy file: {e}")

        # Hardcoded fallback
        return {
            "rules": {
                "ALLOWED_OBJECTS": ["eyeglasses", "water_bottle", "pen", "pencil"],
                "STRICTLY_PROHIBITED": ["smartphone", "laptop", "earbud", "headphones", "smartwatch", "book", "notes"],
                "SEVERITY_MAPPINGS": {
                    "PROHIBITED_DEVICE": "CRITICAL",
                    "MULTIPLE_FACES_DETECTED": "HIGH",
                    "NO_FACE_DETECTED": "HIGH",
                    "DICTATION_OR_COLLUSION_DETECTED": "HIGH",
                    "MULTIPLE_VOICES_DETECTED": "HIGH",
                    "SUSPICIOUS_GAZE": "MEDIUM",
                    "WHISPERING_DETECTED": "MEDIUM"
                },
                "RISK_POINTS": {
                    "CRITICAL": 35.0,
                    "HIGH": 25.0,
                    "MEDIUM": 12.0,
                    "LOW": 5.0
                }
            }
        }

    def _initialize_chroma(self):
        """Initializes ChromaDB vector collection if available."""
        try:
            import chromadb
            client = chromadb.Client()
            self._chroma_collection = client.get_or_create_collection(name="exam_policies")
            logger.info("ChromaDB vector collection initialized successfully.")
        except Exception as e:
            logger.debug(f"ChromaDB local vector client deferred: {e}. Running with JSON policy store.")
            self._chroma_collection = None

    @property
    def strictly_prohibited(self) -> Set[str]:
        rules = self._policy_data.get("rules", {})
        return set(item.lower() for item in rules.get("STRICTLY_PROHIBITED", []))

    @property
    def allowed_objects(self) -> Set[str]:
        rules = self._policy_data.get("rules", {})
        return set(item.lower() for item in rules.get("ALLOWED_OBJECTS", []))

    def is_object_prohibited(self, object_name: str) -> bool:
        """Determines if an object is strictly prohibited by policy."""
        norm_name = object_name.lower().strip().replace(" ", "_")
        if norm_name in self.allowed_objects:
            return False
        for prohibited in self.strictly_prohibited:
            if prohibited in norm_name or norm_name in prohibited:
                return True
        return False

    def get_severity_for_anomaly(self, anomaly_type: str) -> AnomalySeverity:
        """Looks up the institutional severity mapping for an anomaly type."""
        rules = self._policy_data.get("rules", {})
        mapping = rules.get("SEVERITY_MAPPINGS", {})
        raw_sev = mapping.get(anomaly_type, "MEDIUM").upper()
        try:
            return AnomalySeverity(raw_sev)
        except Exception:
            return AnomalySeverity.MEDIUM

    def get_penalty_points(self, severity: AnomalySeverity) -> float:
        """Retrieves risk score penalty points based on breach severity."""
        rules = self._policy_data.get("rules", {})
        points_map = rules.get("RISK_POINTS", {})
        return float(points_map.get(severity.value, 10.0))


# Global policy retriever instance
policy_retriever = PolicyRetriever()
