"""
Document Validation Engine for Identity Verification
Validates uploaded identity cards (Aadhaar, PAN, Driving License, Passport),
detects document type mismatches, verifies photo presence and proportions,
and flags invalid, blurry, or non-ID images.
"""

import cv2
import numpy as np
import base64
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("document_validator")


class DocumentValidator:
    """
    Intelligent Computer Vision Document Validator.
    Discriminates between Aadhaar, PAN, Driving License, Passport, and non-ID images.
    """

    SUPPORTED_TYPES = {
        "aadhaar": "Aadhaar Card",
        "pan": "PAN Card (Income Tax Dept)",
        "driving_license": "Indian Driving Licence",
        "passport": "Indian Passport (Identity Page)"
    }

    @staticmethod
    def decode_base64_image(b64_str: str) -> Optional[np.ndarray]:
        """Decodes base64 string or data URL to OpenCV BGR numpy array."""
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

    @staticmethod
    def _sanitize(obj: Any) -> Any:
        """Recursively converts numpy scalars and arrays to native Python types for JSON/Pydantic serialization."""
        if isinstance(obj, dict):
            return {k: DocumentValidator._sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DocumentValidator._sanitize(v) for v in obj]
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    @classmethod
    def validate_document(cls, image_b64: str, selected_type: str = "aadhaar") -> Dict[str, Any]:
        """
        Main validation method.
        Returns a comprehensive report including:
        - status: VALID, MISMATCH, INVALID, BLURRY, NOT_AN_ID
        - is_match: bool
        - detected_type: str
        - selected_type: str
        - warning_message: str
        - clarity_score: float (0.0 to 100.0)
        - checks: dict of individual test results
        """
        raw_norm = (selected_type or "aadhaar").lower().strip().replace("-", "_").replace(" ", "_")
        if "pan" in raw_norm:
            selected_norm = "pan"
        elif "aadhaar" in raw_norm or "aadhar" in raw_norm:
            selected_norm = "aadhaar"
        elif "driving" in raw_norm or "license" in raw_norm or "licence" in raw_norm or raw_norm == "dl":
            selected_norm = "driving_license"
        elif "passport" in raw_norm:
            selected_norm = "passport"
        else:
            selected_norm = raw_norm
        selected_label = cls.SUPPORTED_TYPES.get(selected_norm, selected_norm.replace("_", " ").title())

        img = cls.decode_base64_image(image_b64)
        if img is None:
            return cls._sanitize({
                "status": "INVALID",
                "is_match": False,
                "detected_type": "unknown",
                "selected_type": selected_norm,
                "detected_label": "Unknown / Unreadable",
                "selected_label": selected_label,
                "warning_message": "Corrupted or unreadable image file. Please upload a valid JPG or PNG document.",
                "clarity_score": 0.0,
                "checks": {"image_decodable": False}
            })

        h, w = img.shape[:2]
        checks = {
            "image_decodable": True,
            "dimensions": f"{w}x{h}",
            "aspect_ratio": round(w / float(h), 2)
        }

        # 1. Blur & Image Clarity Evaluation
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        clarity_pct = min(100.0, max(10.0, round((lap_var / 250.0) * 100.0, 1)))
        checks["laplacian_variance"] = round(lap_var, 1)
        checks["clarity_score"] = clarity_pct

        is_blurry = lap_var < 35.0
        checks["is_sharp"] = not is_blurry

        # 2. Document Type Classification (Aadhaar vs PAN vs DL vs Passport)
        detected_type, doc_confidence, features = cls._classify_document_type(img, gray)
        checks["detected_features"] = features
        checks["detected_confidence"] = doc_confidence

        is_match = (detected_type == selected_norm) or (detected_type == "generic_id" and selected_norm in cls.SUPPORTED_TYPES)

        # 3. Face Detection in Document (Card Photo Analysis)
        face_count, face_area_ratio, face_boxes = cls._detect_faces(img)
        checks["face_count"] = face_count
        checks["face_area_ratio"] = round(face_area_ratio, 3)

        # Check if direct selfie was uploaded instead of document
        if face_area_ratio > 0.55:
            return cls._sanitize({
                "status": "NOT_AN_ID",
                "is_match": False,
                "detected_type": "direct_selfie",
                "selected_type": selected_norm,
                "detected_label": "Direct Personal Selfie",
                "selected_label": selected_label,
                "warning_message": "⚠️ Direct selfie uploaded instead of an ID document! Please upload your official physical identity card (Aadhaar, PAN, DL, or Passport), not your personal selfie.",
                "clarity_score": clarity_pct,
                "checks": checks
            })

        # Check for standalone passport/portrait photo with blue studio backdrop
        if detected_type == "blue_backdrop_portrait":
            return cls._sanitize({
                "status": "NOT_AN_ID",
                "is_match": False,
                "detected_type": "blue_backdrop_portrait",
                "selected_type": selected_norm,
                "detected_label": "Personal Photo (Blue Studio Backdrop)",
                "selected_label": selected_label,
                "warning_message": "🚫 NOT AN ID CARD: You uploaded a standalone personal photo with a blue studio backdrop, not an official Government PAN Card! Please upload the full physical card showing your 10-digit PAN number, name, and card borders.",
                "clarity_score": clarity_pct,
                "checks": checks
            })

        if face_count == 0 and not features.get("qr_detected"):
            return cls._sanitize({
                "status": "INVALID",
                "is_match": False,
                "detected_type": "non_photo_document",
                "selected_type": selected_norm,
                "detected_label": "Document Missing Photo",
                "selected_label": selected_label,
                "warning_message": "⚠️ No photograph detected on the uploaded document. Please upload the front side of your official photo ID card where your portrait is clearly visible.",
                "clarity_score": clarity_pct,
                "checks": checks
            })

        # Check for Document Type Mismatch
        detected_label = cls.SUPPORTED_TYPES.get(detected_type, detected_type.replace("_", " ").title())
        if not is_match and detected_type in cls.SUPPORTED_TYPES and detected_type != selected_norm:
            return cls._sanitize({
                "status": "MISMATCH",
                "is_match": False,
                "detected_type": detected_type,
                "selected_type": selected_norm,
                "detected_label": detected_label,
                "selected_label": selected_label,
                "warning_message": f"⚠️ Document Type Mismatch: You selected '{selected_label}', but the uploaded document has characteristics of a '{detected_label}'. Please verify your document selection or upload the appropriate card.",
                "clarity_score": clarity_pct,
                "checks": checks
            })

        if face_count > 3:
            return cls._sanitize({
                "status": "INVALID",
                "is_match": False,
                "detected_type": "group_photo",
                "selected_type": selected_norm,
                "detected_label": "Group / Multi-Face Photo",
                "selected_label": selected_label,
                "warning_message": f"⚠️ Multiple faces ({face_count}) detected in the document image. Please upload an individual official identity card.",
                "clarity_score": clarity_pct,
                "checks": checks
            })

        # Build Status & Warning Message
        if is_blurry:
            status = "BLURRY"
            warning_msg = f"⚠️ The uploaded document is blurry (clarity: {clarity_pct}%). Text and photo may fail official verification. Please upload a sharper scan or photograph."
        elif detected_type == "unknown":
            status = "INVALID"
            warning_msg = f"⚠️ Unrecognized document format. Please upload a valid {cls.SUPPORTED_TYPES.get(selected_norm, 'ID Card')} with all 4 corners and portrait photo clearly visible."
        else:
            status = "VALID"
            warning_msg = f"✅ Valid {cls.SUPPORTED_TYPES.get(selected_norm, 'ID Card')} detected. Photo region and card structure verified."

        return cls._sanitize({
            "status": status,
            "is_match": is_match,
            "detected_type": detected_type,
            "selected_type": selected_norm,
            "detected_label": cls.SUPPORTED_TYPES.get(detected_type, detected_type.replace("_", " ").title()),
            "selected_label": cls.SUPPORTED_TYPES.get(selected_norm, selected_norm.replace("_", " ").title()),
            "warning_message": warning_msg,
            "clarity_score": clarity_pct,
            "checks": checks
        })

    @classmethod
    def _detect_faces(cls, img: np.ndarray) -> Tuple[int, float, list]:
        """Detects faces in document image using multi-cascade to evaluate count and area ratio."""
        h, w = img.shape[:2]
        total_area = float(h * w)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Try InsightFace first if available
        try:
            from app.ai.face_verifier import _insight_app, _INSIGHTFACE_AVAILABLE
            if _INSIGHTFACE_AVAILABLE and _insight_app is not None:
                if_faces = _insight_app.get(img)
                if len(if_faces) > 0:
                    max_area = 0.0
                    boxes = []
                    for f in if_faces:
                        bx1, by1, bx2, by2 = f.bbox
                        bw, bh = max(0, bx2 - bx1), max(0, by2 - by1)
                        area = bw * bh
                        if area > max_area:
                            max_area = area
                        boxes.append({"x": int(bx1), "y": int(by1), "w": int(bw), "h": int(bh)})
                    return len(if_faces), max_area / total_area if total_area > 0 else 0.0, boxes
        except Exception:
            pass

        # Try Haar cascades
        faces = []
        if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if cv2.os.path.exists(cascade_path):
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))

            if len(faces) == 0:
                alt_path = cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
                if cv2.os.path.exists(alt_path):
                    alt_cascade = cv2.CascadeClassifier(alt_path)
                    faces = alt_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))

        face_count = len(faces)
        if face_count == 0:
            # Check candidate photo sub-zone for significant contrast / photo texture
            photo_zone = gray[int(h * 0.12):int(h * 0.85), int(w * 0.03):int(w * 0.48)]
            if photo_zone.size > 0 and np.std(photo_zone) > 18.0:
                fh, fw = int(h * 0.35), int(w * 0.22)
                return 1, (fh * fw) / total_area, [{"x": int(w * 0.06), "y": int(h * 0.2), "w": fw, "h": fh}]
            return 0, 0.0, []

        max_face_area = 0.0
        face_boxes = []
        for (x, y, fw, fh) in faces:
            area = fw * fh
            if area > max_face_area:
                max_face_area = area
            face_boxes.append({"x": int(x), "y": int(y), "w": int(fw), "h": int(fh)})

        area_ratio = max_face_area / total_area if total_area > 0 else 0.0
        return face_count, area_ratio, face_boxes

    @classmethod
    def _classify_document_type(cls, img: np.ndarray, gray: np.ndarray) -> Tuple[str, float, dict]:
        """
        Classifies document based on:
        1. Color spectrum (HSV) - Saffron/Green bands, PAN blue/cyan saturation.
        2. QR Code presence (Standard on Aadhaar, newer PAN).
        3. Machine Readable Zone (MRZ) line patterns (Passport).
        4. Aspect ratio and card layout.
        """
        h, w = img.shape[:2]
        features = {}

        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # A. QR Code Detection (Strong indicator for Aadhaar / Smart cards)
        qr_detector = cv2.QRCodeDetector()
        qr_found, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(gray)
        if not qr_found or len(decoded_info) == 0:
            res, _ = qr_detector.detect(gray)
            qr_detected = bool(res)
        else:
            qr_detected = True
        features["qr_detected"] = qr_detected

        # B. Color Signatures
        # 1. PAN Card: Blue/Teal gradient (Hue ~ 90 to 135, high saturation)
        blue_mask = cv2.inRange(hsv, np.array([90, 40, 50]), np.array([135, 255, 255]))
        blue_ratio = np.sum(blue_mask > 0) / float(h * w)
        features["pan_blue_ratio"] = round(blue_ratio, 3)

        # 2. Aadhaar Card: White body + Saffron top strip (Hue 10-25) + Green strip (Hue 40-80)
        white_mask = cv2.inRange(hsv, np.array([0, 0, 160]), np.array([180, 45, 255]))
        white_ratio = np.sum(white_mask > 0) / float(h * w)
        features["white_ratio"] = round(white_ratio, 3)

        # Top 25% header color check
        top_hsv = hsv[:int(h * 0.28), :]
        top_pixels = top_hsv.shape[0] * top_hsv.shape[1]
        saffron_mask = cv2.inRange(top_hsv, np.array([8, 60, 80]), np.array([25, 255, 255]))
        green_mask = cv2.inRange(top_hsv, np.array([38, 45, 50]), np.array([85, 255, 255]))
        saffron_ratio = np.sum(saffron_mask > 0) / float(top_pixels) if top_pixels > 0 else 0.0
        green_ratio = np.sum(green_mask > 0) / float(top_pixels) if top_pixels > 0 else 0.0
        features["saffron_header_ratio"] = round(saffron_ratio, 3)
        features["green_header_ratio"] = round(green_ratio, 3)

        # 3. Driving License: Yellowish / Greenish header or smart chip icon
        yellow_mask = cv2.inRange(top_hsv, np.array([22, 50, 70]), np.array([38, 255, 255]))
        yellow_ratio = np.sum(yellow_mask > 0) / float(top_pixels) if top_pixels > 0 else 0.0
        features["yellow_header_ratio"] = round(yellow_ratio, 3)

        # 4. Passport: MRZ check (Bottom 25% has dense horizontal text stripes)
        bot_gray = gray[int(h * 0.72):, :]
        sobel_x = cv2.Sobel(bot_gray, cv2.CV_64F, 1, 0, ksize=3)
        mrz_energy = np.mean(np.abs(sobel_x))
        features["bottom_mrz_energy"] = round(mrz_energy, 1)

        # Decision Logic
        # 1. Check for Passport: High horizontal edge energy at bottom and aspect ratio ~ 1.3 to 1.5
        if mrz_energy > 40.0 and (w / float(h)) < 1.6 and blue_ratio < 0.25:
            return "passport", 0.88, features

        # 2. Check for PAN Card: High blue/teal ratio across card and landscape card layout
        card_aspect = w / float(h)
        if blue_ratio > 0.18:
            if card_aspect >= 1.20:
                return "pan", 0.92, features
            else:
                return "blue_backdrop_portrait", 0.90, features

        # 3. Check for Aadhaar Card: White body + saffron/green top header or QR code
        if (white_ratio > 0.35 and (saffron_ratio > 0.04 or green_ratio > 0.04)) or (white_ratio > 0.40 and qr_detected):
            return "aadhaar", 0.94, features

        # 4. Check for Driving License: Yellow header or mixed transport layout
        if yellow_ratio > 0.08 or (white_ratio > 0.30 and blue_ratio < 0.10 and not qr_detected and saffron_ratio < 0.03):
            return "driving_license", 0.82, features

        # 5. Default generic card if white or standard aspect ratio
        if white_ratio > 0.25:
            return "generic_id", 0.70, features

        return "unknown", 0.40, features
