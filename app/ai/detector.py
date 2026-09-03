import os
import logging
import cv2
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger("app.ai.detector")

class AIDetector:
    """
    Multi-stage AI Object and Person Detector supporting:
    1. Ultralytics YOLOv8 object detection (PyTorch) with sensitive conf=0.25
    2. Multi-object color-coded keyframe annotation
    3. Non-Maximum Suppression & IoA box deduplication for single person enforcement
    4. OpenCV Multi-Cascade Face & Upper Body detection fallbacks
    5. Head/Skin contour analysis fallback
    """
    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model_name = model_name
        self.yolo_model = None
        self.cascades = []
        self._init_models()

    def _init_models(self):
        # 1. Primary: Attempt YOLOv8 import
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(self.model_name)
            logger.info(f"YOLOv8 model ({self.model_name}) loaded successfully.")
        except Exception as e:
            logger.warning(f"YOLOv8 model not loaded ({e}). Using OpenCV multi-cascade & vision pipelines.")
            self.yolo_model = None

        # 2. Secondary: Load OpenCV Cascades if supported
        cascade_files = [
            "haarcascade_frontalface_default.xml",
            "haarcascade_frontalface_alt.xml",
            "haarcascade_frontalface_alt2.xml",
            "haarcascade_profileface.xml",
            "haarcascade_upperbody.xml"
        ]
        
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            for fname in cascade_files:
                path = os.path.join(cv2.data.haarcascades, fname)
                if os.path.exists(path):
                    try:
                        cascade = cv2.CascadeClassifier(path)
                        if not cascade.empty():
                            self.cascades.append((fname, cascade))
                    except Exception as err:
                        logger.warning(f"Could not load cascade {fname}: {err}")
        
        if self.cascades:
            logger.info(f"Loaded {len(self.cascades)} OpenCV cascades for detection.")

    def detect(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Runs object detection on BGR image matrix.
        Returns standardized dictionary containing all predicted objects.
        """
        detections: List[Dict[str, Any]] = []

        if image is None or image.size == 0:
            return {"detections": detections}

        # 1. Primary: YOLOv8 Inference with conf=0.25 to capture handheld phones & small objects
        if self.yolo_model is not None:
            try:
                results = self.yolo_model(image, conf=0.25, verbose=False)
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        class_name = self.yolo_model.names[cls_id]
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        
                        # Normalize phone labels
                        if class_name in ["cell phone", "remote", "telephone", "mobile"]:
                            class_name = "cell phone"

                        detections.append({
                            "object": class_name,
                            "confidence": round(conf, 2),
                            "bounding_box": xyxy
                        })
                if detections:
                    # Suppress duplicate person detections for single candidate while keeping phone detections intact
                    detections = self._merge_duplicate_person_boxes(detections)
                    return {"detections": detections}
            except Exception as e:
                logger.error(f"Error during YOLO inference: {e}")

        # 2. Secondary: Multi-Cascade Face & Body Detection
        if self.cascades:
            raw_boxes = []
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            for fname, cascade in self.cascades:
                min_size = (60, 60) if "upperbody" in fname else (30, 30)
                scale = 1.1 if "frontalface" in fname else 1.15
                
                found = cascade.detectMultiScale(gray, scaleFactor=scale, minNeighbors=4, minSize=min_size)
                for (x, y, w, h) in found:
                    if "face" in fname:
                        pad_w = int(w * 0.3)
                        pad_h = int(h * 0.5)
                        x1 = max(0, x - pad_w)
                        y1 = max(0, y - pad_h)
                        x2 = min(image.shape[1], x + w + pad_w)
                        y2 = min(image.shape[0], y + h + pad_h * 2)
                    else:
                        x1, y1, x2, y2 = x, y, x + w, y + h

                    raw_boxes.append([x1, y1, x2, y2])

            if raw_boxes:
                merged_boxes = self._non_max_suppression(np.array(raw_boxes), overlapThresh=0.4)
                for (x1, y1, x2, y2) in merged_boxes:
                    detections.append({
                        "object": "person",
                        "confidence": 0.88,
                        "bounding_box": [int(x1), int(y1), int(x2), int(y2)]
                    })
                detections = self._merge_duplicate_person_boxes(detections)
                return {"detections": detections}

        # 3. Fallback: Skin tone & Head Contour Detection
        skin_box = self._detect_head_skin_contour(image)
        if skin_box:
            detections.append({
                "object": "person",
                "confidence": 0.75,
                "bounding_box": skin_box
            })

        return {"detections": detections}

    @staticmethod
    def _merge_duplicate_person_boxes(detections: List[Dict[str, Any]], iou_thresh: float = 0.30, ioa_thresh: float = 0.45) -> List[Dict[str, Any]]:
        """
        Deduplicates overlapping 'person' detections to ensure 1 candidate generates 1 person box,
        without touching non-person detections like 'cell phone'.
        """
        person_dets = [d for d in detections if d.get("object") == "person"]
        other_dets = [d for d in detections if d.get("object") != "person"]

        if len(person_dets) <= 1:
            return detections

        boxes = np.array([p["bounding_box"] for p in person_dets], dtype=float)
        confs = np.array([p["confidence"] for p in person_dets])

        order = np.argsort(confs)[::-1]
        keep = []

        while len(order) > 0:
            idx = order[0]
            keep.append(person_dets[idx])
            if len(order) == 1:
                break

            current_box = boxes[idx]
            other_indices = order[1:]
            other_boxes = boxes[other_indices]

            xx1 = np.maximum(current_box[0], other_boxes[:, 0])
            yy1 = np.maximum(current_box[1], other_boxes[:, 1])
            xx2 = np.minimum(current_box[2], other_boxes[:, 2])
            yy2 = np.minimum(current_box[3], other_boxes[:, 3])

            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            inter = w * h

            area_current = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
            area_others = (other_boxes[:, 2] - other_boxes[:, 0]) * (other_boxes[:, 3] - other_boxes[:, 1])

            union = area_current + area_others - inter
            iou = inter / np.maximum(union, 1e-6)
            ioa = inter / np.maximum(np.minimum(area_current, area_others), 1e-6)

            suppress = (iou > iou_thresh) | (ioa > ioa_thresh)
            order = other_indices[~suppress]

        return keep + other_dets

    @staticmethod
    def _non_max_suppression(boxes: np.ndarray, overlapThresh: float = 0.4) -> List[List[int]]:
        """Non-Maximum Suppression to merge overlapping bounding boxes."""
        if len(boxes) == 0:
            return []
        
        if boxes.dtype.kind == "i":
            boxes = boxes.astype("float")

        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)

        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)

            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])

            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)

            overlap = (w * h) / area[idxs[:last]]
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

        return boxes[pick].astype("int").tolist()

    @staticmethod
    def _detect_head_skin_contour(image: np.ndarray) -> List[int]:
        """Detects presence of candidate via HSV skin-tone contouring."""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)

            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
            mask = cv2.erode(mask, kernel, iterations=2)
            mask = cv2.dilate(mask, kernel, iterations=2)
            mask = cv2.GaussianBlur(mask, (3, 3), 0)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h, w, _ = image.shape
            min_area = (w * h) * 0.03

            valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
            if valid_contours:
                largest = max(valid_contours, key=cv2.contourArea)
                x, y, bw, bh = cv2.boundingRect(largest)
                return [int(x), int(y), int(x + bw), int(y + bh)]
        except Exception:
            pass
        return []

    @staticmethod
    def annotate_frame(image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draws color-coded bounding boxes and labels for ALL detected objects simultaneously onto cloned BGR image frame.
        - Red: Cell Phone / Mobile
        - Orange/Amber: Person
        - Purple: Secondary Devices (Laptop/TV/Remote)
        """
        annotated = image.copy()
        
        # Color Map (BGR format)
        COLOR_MAP = {
            "cell phone": (0, 0, 255),       # Bright Red
            "phone": (0, 0, 255),            # Bright Red
            "person": (0, 165, 255),         # Orange/Amber
            "laptop": (255, 0, 255),         # Magenta/Purple
            "tv": (255, 0, 255),             # Magenta/Purple
            "remote": (0, 0, 255),           # Bright Red
            "default": (0, 255, 255)         # Yellow
        }

        for det in detections:
            bbox = det.get("bounding_box")
            obj_name = det.get("object", "violation").lower()
            conf = det.get("confidence", 0.0)

            color = COLOR_MAP.get(obj_name, COLOR_MAP["default"])

            if bbox and len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                # Draw thick bounding rectangle
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                label_text = f"{obj_name.upper()} {conf:.2f}"
                (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                
                # Filled background banner for label text
                text_y = max(y1, 25)
                cv2.rectangle(annotated, (x1, text_y - 20), (x1 + w + 10, text_y + 4), color, -1)
                cv2.putText(annotated, label_text, (x1 + 5, text_y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        return annotated

# Global Singleton Detector instance
detector = AIDetector()
