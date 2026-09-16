"""
Identity Verification Service Module
Biometric face comparison between government ID document and live webcam capture
with Human-in-the-Loop triage fallback for uncertain/borderline matches.
"""

import cv2
import base64
import logging
import numpy as np
from typing import Tuple, Optional, Dict, Any

from src.core.config import settings
from src.features.identity_verification.schemas import (
    IdentityVerificationRequest,
    IdentityVerificationResponse,
    VerificationStatus
)

logger = logging.getLogger("identity_verification_service")


class IdentityVerificationService:
    """
    Handles pre-exam candidate biometric identity validation.
    Enforces a strict Human-in-the-Loop review threshold to eliminate false disqualifications.
    """

    @staticmethod
    def decode_base64_image(b64_str: str) -> Optional[np.ndarray]:
        """Converts base64 string or data URL to OpenCV BGR numpy array."""
        try:
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_str)
            nparr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    @classmethod
    def extract_face_embedding(cls, img: np.ndarray) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Extracts 512-dimensional facial embedding using InsightFace ArcFace.
        Gracefully falls back to normalized histogram/spatial visual features if running in offline test mode.
        """
        metadata = {"detector": "insightface", "embedding_dim": 512}
        
        try:
            from app.ai.face_verifier import _insight_app, _INSIGHTFACE_AVAILABLE
            if _INSIGHTFACE_AVAILABLE and _insight_app is not None:
                faces = _insight_app.get(img)
                if len(faces) > 0:
                    # Select largest face by area
                    best_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
                    norm_embedding = best_face.embedding / np.linalg.norm(best_face.embedding)
                    metadata["face_box"] = [int(v) for v in best_face.bbox]
                    return norm_embedding, metadata
        except Exception as e:
            logger.debug(f"InsightFace direct extraction skipped: {e}")

        # Fallback multi-scale feature descriptor for test and lightweight environments
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (112, 112))
        features = resized.astype(np.float32).flatten()
        norm_val = np.linalg.norm(features)
        if norm_val > 0:
            features = features / norm_val
        metadata["detector"] = "spatial_fallback"
        metadata["embedding_dim"] = len(features)
        return features, metadata

    @classmethod
    def compute_similarity(cls, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Computes cosine similarity between two normalized feature vectors."""
        if emb1 is None or emb2 is None:
            return 0.0
        dot_product = float(np.dot(emb1, emb2))
        return max(0.0, min(1.0, dot_product))

    @classmethod
    def verify_candidate_identity(
        cls,
        request: IdentityVerificationRequest
    ) -> IdentityVerificationResponse:
        """
        Main entry point for verifying a candidate's identity prior to exam commencement.
        Integrates FaceVerifier with document-adaptive ROI extraction (Aadhaar, PAN, DL, Passport)
        and ArcFace confidence calibration, backed by Human-in-the-Loop triage.
        
        Thresholds:
        - >= 70% (0.70): VERIFIED (Automated clearance)
        - 40% - 69.9% (0.40 to 0.699): PENDING_HUMAN_REVIEW (Escalated to human proctor)
        - < 40% (< 0.40): REJECTED (Definite mismatch)
        """
        doc_img = cls.decode_base64_image(request.document_image_b64)
        selfie_img = cls.decode_base64_image(request.selfie_image_b64)

        if doc_img is None or selfie_img is None:
            return IdentityVerificationResponse(
                candidate_id=request.candidate_id,
                status=VerificationStatus.REJECTED,
                verified=False,
                match_confidence=0.0,
                match_percentage="0.0%",
                document_type=request.document_type,
                needs_human_review=False,
                review_reason="Image payload could not be decoded. Ensure valid JPG/PNG base64 inputs.",
                audit_metadata={"error": "DECODING_FAILED"}
            )

        # Normalize document type for ROI extraction prior
        raw_type = (request.document_type or "aadhaar").lower().replace("_card", "").replace("s_license", "").strip()
        if "passport" in raw_type:
            mapped_doc = "passport"
        elif "driver" in raw_type or "dl" in raw_type:
            mapped_doc = "driving_license"
        elif "pan" in raw_type:
            mapped_doc = "pan"
        else:
            mapped_doc = "aadhaar"

        # Check document structural validity via DocumentValidator if available
        doc_validation_report = None
        try:
            from app.ai.document_validator import DocumentValidator
            doc_validation_report = DocumentValidator.validate_document(
                request.document_image_b64,
                selected_type=mapped_doc
            )
        except Exception as err:
            logger.debug(f"DocumentValidator check skipped: {err}")

        # Run FaceVerifier comparing document photo ROI vs live selfie
        verif_result = None
        try:
            from app.ai.face_verifier import FaceVerifier
            verif_result = FaceVerifier.compare_faces(doc_img, selfie_img, doc_type=mapped_doc)
        except Exception as e:
            logger.warning(f"FaceVerifier direct invocation error: {e}")

        if verif_result and "match_confidence" in verif_result:
            confidence = float(verif_result["match_confidence"])
            match_pct_str = verif_result.get("match_percentage", f"{confidence * 100:.1f}%")
            verified_flag = bool(verif_result.get("verified", False))
            detail_msg = verif_result.get("detail", "")
            meta_doc = {"backend": verif_result.get("backend", "FaceVerifier"), "doc_type": mapped_doc}
            meta_selfie = {"similarity": verif_result.get("deep_embedding_similarity", confidence)}
        else:
            emb_doc, meta_doc = cls.extract_face_embedding(doc_img)
            emb_selfie, meta_selfie = cls.extract_face_embedding(selfie_img)
            confidence = cls.compute_similarity(emb_doc, emb_selfie)
            match_pct_str = f"{confidence * 100:.1f}%"
            verified_flag = confidence >= settings.MIN_FACE_MATCH_THRESHOLD
            detail_msg = ""

        # Apply Tri-State Human-in-the-Loop Decision Policy
        if confidence >= settings.MIN_FACE_MATCH_THRESHOLD or verified_flag:
            status = VerificationStatus.VERIFIED
            verified = True
            needs_human = False
            reason = detail_msg or f"Biometric match successfully validated above 70.0% threshold ({match_pct_str})."
        elif confidence >= settings.HUMAN_REVIEW_MATCH_THRESHOLD:
            status = VerificationStatus.PENDING_HUMAN_REVIEW
            verified = False
            needs_human = True
            reason = (
                detail_msg or 
                f"Borderline match score ({match_pct_str}) falls in the review corridor "
                f"({settings.HUMAN_REVIEW_MATCH_THRESHOLD*100:.0f}%-{settings.MIN_FACE_MATCH_THRESHOLD*100:.0f}%). "
                f"Escalated for human proctor sign-off to prevent false disqualification."
            )
        else:
            status = VerificationStatus.REJECTED
            verified = False
            needs_human = False
            reason = (
                detail_msg or 
                f"Biometric similarity ({match_pct_str}) is below the minimum threshold. "
                f"Face on ID card does not correspond to live webcam capture."
            )

        audit_meta = {
            "doc_metadata": meta_doc,
            "selfie_metadata": meta_selfie,
            "thresholds": {
                "auto_verify": settings.MIN_FACE_MATCH_THRESHOLD,
                "human_review": settings.HUMAN_REVIEW_MATCH_THRESHOLD
            }
        }
        if doc_validation_report:
            audit_meta["document_validation"] = doc_validation_report

        return IdentityVerificationResponse(
            candidate_id=request.candidate_id,
            status=status,
            verified=verified,
            match_confidence=round(confidence, 4),
            match_percentage=match_pct_str,
            document_type=request.document_type,
            needs_human_review=needs_human,
            review_reason=reason,
            audit_metadata=audit_meta
        )
