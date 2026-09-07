import cv2
import numpy as np
import pytest
from app.ai.face_verifier import FaceVerifier, extract_deep_face_embedding

def create_synthetic_person_face(color=(130, 160, 210), scale=1.0, brightness=1.0, add_aging_features=False) -> np.ndarray:
    """
    Generates realistic synthetic facial structure.
    - color: Base skin/feature color tuple (B, G, R)
    - scale: Face size / jaw structure scaling
    - brightness: Illumination factor (1.0 = normal, 0.25 = dim/dark room)
    - add_aging_features: Adds subtle age structural shifts & wrinkles
    """
    h, w = 300, 300
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    center_x, center_y = 150, 150
    axes_w = int(60 * scale)
    axes_h = int(80 * scale)

    # Adjusted color based on brightness
    adj_color = tuple([int(c * brightness) for c in color])
    
    # 1. Base Face Shape
    cv2.ellipse(img, (center_x, center_y), (axes_w, axes_h), 0, 0, 360, adj_color, -1)
    
    # 2. Eye Landmarks (invariant bone structure distance)
    eye_y = int(center_y - 20 * scale)
    eye_x_left = int(center_x - 22 * scale)
    eye_x_right = int(center_x + 22 * scale)
    eye_color = tuple([int(240 * brightness)] * 3)
    cv2.circle(img, (eye_x_left, eye_y), int(8 * scale), eye_color, -1)
    cv2.circle(img, (eye_x_right, eye_y), int(8 * scale), eye_color, -1)
    
    # 3. Nose Bridge Line
    nose_color = tuple([int(180 * brightness)] * 3)
    cv2.line(img, (center_x, eye_y), (center_x, center_y + int(15 * scale)), nose_color, int(3 * scale))
    
    # 4. Aging features (Wrinkles / hairline / skin tone texture shift)
    if add_aging_features:
        wrinkle_color = tuple([int(60 * brightness)] * 3)
        # Forehead lines
        cv2.line(img, (center_x - 30, center_y - 45), (center_x + 30, center_y - 45), wrinkle_color, 1)
        cv2.line(img, (center_x - 25, center_y - 35), (center_x + 25, center_y - 35), wrinkle_color, 1)
        # Nasolabial folds
        cv2.line(img, (center_x - 15, center_y + 15), (center_x - 30, center_y + 40), wrinkle_color, 1)
        cv2.line(img, (center_x + 15, center_y + 15), (center_x + 30, center_y + 40), wrinkle_color, 1)
        
    return img


def test_baseline_same_person_normal_lighting():
    """Verify same person under normal lighting achieves high confidence (>=90%)."""
    doc_photo = create_synthetic_person_face(color=(130, 160, 210), brightness=1.0)
    selfie_photo = create_synthetic_person_face(color=(130, 160, 210), brightness=0.95)

    res = FaceVerifier.compare_faces(doc_photo, selfie_photo)
    print(f"\n[TEST 1 - Baseline Normal Light] Match Confidence: {res['match_percentage']} | Verified: {res['verified']}")
    
    assert res["verified"] is True
    assert res["match_confidence"] >= 0.90


def test_same_person_with_age_gap():
    """Verify same person with significant age gap (younger Aadhaar photo vs older selfie) passes >=90%."""
    # ID photo: Younger face (no aging lines, smooth skin texture)
    doc_id_young = create_synthetic_person_face(color=(130, 160, 210), scale=0.95, brightness=1.0, add_aging_features=False)
    
    # Live Selfie: Older face (aging lines, structural maturity shift)
    selfie_older = create_synthetic_person_face(color=(120, 150, 200), scale=1.05, brightness=0.90, add_aging_features=True)

    res = FaceVerifier.compare_faces(doc_id_young, selfie_older)
    print(f"\n[TEST 2 - Age Gap] Match Confidence: {res['match_percentage']} | Deep Embedding Similarity: {res['deep_embedding_similarity']} | Verified: {res['verified']}")
    
    assert res["verified"] is True, f"Age gap comparison failed: {res}"
    assert res["match_confidence"] >= 0.90


def test_same_person_dim_room_lighting():
    """Verify same person in dark/dim room lighting (low illumination webcam) passes >=90%."""
    doc_id_normal = create_synthetic_person_face(color=(130, 160, 210), brightness=1.0)
    
    # Live Selfie: Dim room light (25% brightness) with shadow gradient
    selfie_dim_light = create_synthetic_person_face(color=(130, 160, 210), brightness=0.25)
    
    res = FaceVerifier.compare_faces(doc_id_normal, selfie_dim_light)
    print(f"\n[TEST 3 - Dim Lighting] Match Confidence: {res['match_percentage']} | Deep Embedding Similarity: {res['deep_embedding_similarity']} | Verified: {res['verified']}")
    
    assert res["verified"] is True, f"Dim lighting comparison failed: {res}"
    assert res["match_confidence"] >= 0.90


def test_same_person_combined_age_gap_and_dim_lighting():
    """Verify same person with BOTH age gap AND dim room lighting passes >=90%."""
    # ID photo: Younger person under bright lighting (Aadhaar photo)
    doc_id_young = create_synthetic_person_face(color=(130, 160, 210), scale=0.95, brightness=1.0, add_aging_features=False)
    
    # Live Selfie: Older person in dim dark room lighting (webcam)
    selfie_older_dim = create_synthetic_person_face(color=(125, 155, 205), scale=1.05, brightness=0.30, add_aging_features=True)

    res = FaceVerifier.compare_faces(doc_id_young, selfie_older_dim)
    print(f"\n[TEST 4 - Combined Age Gap + Dim Light] Match Confidence: {res['match_percentage']} | Deep Embedding Similarity: {res['deep_embedding_similarity']} | Verified: {res['verified']}")
    
    assert res["verified"] is True, f"Combined Age Gap + Dim Light comparison failed: {res}"
    assert res["match_confidence"] >= 0.90

def create_different_person_face(brightness=1.0) -> np.ndarray:
    """
    Creates a structurally DIFFERENT person's face.
    Key geometry differences from create_synthetic_person_face:
      - Square/rectangular jaw instead of elliptical
      - Eyes at different vertical position (higher)
      - Eyes much wider apart
      - Wide triangular nose instead of thin line
      - Mouth feature (thick horizontal bar)
      - Different head-to-face ratio
    These geometric differences produce measurably different Sobel gradients.
    """
    h, w = 300, 300
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    adj = lambda v: int(v * brightness)
    
    # Square jawline (very different from ellipse)
    pts = np.array([
        [80, 60], [220, 60],   # forehead (wide)
        [230, 200],             # right jaw
        [200, 250],             # right chin
        [100, 250],             # left chin
        [70, 200],              # left jaw
    ], np.int32)
    cv2.fillPoly(img, [pts], (adj(80), adj(120), adj(170)))
    
    # Eyes: wider apart, higher, smaller (different from Person A's big circles)
    cv2.ellipse(img, (105, 110), (12, 6), 0, 0, 360, (adj(220), adj(220), adj(220)), -1)  # left
    cv2.ellipse(img, (195, 110), (12, 6), 0, 0, 360, (adj(220), adj(220), adj(220)), -1)  # right
    # Pupils
    cv2.circle(img, (105, 110), 3, (adj(40), adj(40), adj(40)), -1)
    cv2.circle(img, (195, 110), 3, (adj(40), adj(40), adj(40)), -1)
    
    # Wide triangular nose (different from thin line)
    nose_pts = np.array([[150, 120], [135, 180], [165, 180]], np.int32)
    cv2.fillPoly(img, [nose_pts], (adj(100), adj(140), adj(190)))
    
    # Thick mouth (Person A has no mouth)
    cv2.ellipse(img, (150, 210), (30, 8), 0, 0, 360, (adj(60), adj(80), adj(130)), -1)
    
    # Eyebrows (thick horizontal bars)
    cv2.rectangle(img, (85, 90), (125, 97), (adj(50), adj(70), adj(100)), -1)
    cv2.rectangle(img, (175, 90), (215, 97), (adj(50), adj(70), adj(100)), -1)
    
    return img


def test_authenticity_different_person_impersonator_rejected():
    """Authenticity check: verify that a clearly different person (impersonator) is REJECTED (<70%).
    
    Person A: Elliptical face, round eyes, thin nose line
    Person B: Square jaw, elliptical eyes, triangular nose, thick mouth, eyebrows
    
    These are structurally very different faces that should produce different Sobel gradient maps.
    """
    # Candidate ID photo — Person A (elliptical face structure)
    doc_candidate = create_synthetic_person_face(color=(130, 160, 210), scale=1.0, brightness=1.0)

    # Impersonator — Person B: completely different facial geometry
    impersonator = create_different_person_face(brightness=1.0)

    res = FaceVerifier.compare_faces(doc_candidate, impersonator)
    print(f"\n[TEST 5 - Authenticity Impersonator Check] Match Confidence: {res['match_percentage']} | Verified: {res['verified']}")
    print(f"  Detail: {res['detail']}")

    assert res["verified"] is False, f"Impersonator was incorrectly verified! {res}"
    assert res["match_confidence"] < 0.70
