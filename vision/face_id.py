"""
Face Identification
═══════════════════
Uses face_recognition library with face_distance for best-match accuracy.
Extracted from robot_merged.py lines 131–169.
"""

import face_recognition
import config
from data.face_db import FaceDB


def identify(rgb_frame, face_location) -> tuple:
    """
    Identify a face at the given location.

    Parameters
    ----------
    rgb_frame : ndarray    – full RGB frame
    face_location : tuple  – (top, right, bottom, left) in full-frame coords

    Returns
    -------
    (name: str, category: str, encoding: ndarray | None)
    category is one of: "permanent", "visitor", "unknown"
    """
    encs = face_recognition.face_encodings(rgb_frame, [face_location])
    if not encs:
        return "Unknown", "unknown", None

    enc = encs[0]
    best_name     = "Unknown"
    best_category = "unknown"
    best_distance = 999.0

    db = FaceDB()

    # Check permanent faces
    perm_enc, perm_names = db.permanent_encodings, db.permanent_names
    if perm_enc:
        distances = face_recognition.face_distance(perm_enc, enc)
        idx  = distances.argmin()
        dist = distances[idx]
        if dist < config.FACE_TOLERANCE:
            best_name     = perm_names[idx]
            best_category = "permanent"
            best_distance = dist

    # Check visitor faces
    vis_enc, vis_names = db.visitor_encodings, db.visitor_names
    if vis_enc:
        distances = face_recognition.face_distance(vis_enc, enc)
        idx  = distances.argmin()
        dist = distances[idx]
        if dist < config.FACE_TOLERANCE and dist < best_distance:
            best_name     = vis_names[idx]
            best_category = "visitor"
            best_distance = dist

    return best_name, best_category, enc


def get_unknown_fingerprint(encoding, unknown_cooldowns: list) -> int | None:
    """
    Check if encoding matches any entry in the cooldown list.
    Returns the index if found, None otherwise.
    """
    for i, (stored_enc, _) in enumerate(unknown_cooldowns):
        if face_recognition.compare_faces(
            [stored_enc], encoding, tolerance=config.FACE_TOLERANCE
        )[0]:
            return i
    return None


def detect_faces_in_roi(roi_rgb) -> list:
    """
    Detect face locations in an ROI using HOG model.
    Returns list of (top, right, bottom, left) tuples.
    """
    return face_recognition.face_locations(roi_rgb, model="hog")
