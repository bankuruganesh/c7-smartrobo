"""
Human Tracker — Bounding-Box Centering & Approach Logic
════════════════════════════════════════════════════════
NEW capability: enables the robot to steer toward a detected
person, keep them centered, and determine when to stop.
"""

import config


def compute_steering(bbox, frame_width: int) -> tuple[str, int]:
    """
    Determine motor steering to center a person in frame.

    Parameters
    ----------
    bbox : Detection namedtuple with x1, y1, x2, y2
    frame_width : int — width of the camera frame

    Returns
    -------
    (direction: str, offset: int)
    direction: "LEFT", "RIGHT", or "CENTER"
    offset: pixels from frame center (always positive)
    """
    person_cx = (bbox.x1 + bbox.x2) // 2
    frame_cx  = frame_width // 2
    offset    = person_cx - frame_cx

    tolerance = config.APPROACH_CENTER_TOLERANCE

    if offset < -tolerance:
        return "LEFT", abs(offset)
    elif offset > tolerance:
        return "RIGHT", abs(offset)
    else:
        return "CENTER", abs(offset)


def should_approach(bbox, frame_height: int) -> bool:
    """
    Returns True if the person is still far away and the robot
    should continue driving forward.

    Uses bbox height as a proxy for distance — a taller bbox means
    the person is closer.
    """
    bbox_height = bbox.y2 - bbox.y1
    ratio = bbox_height / frame_height
    return ratio < config.APPROACH_CLOSE_RATIO


def is_close_enough(bbox, frame_height: int) -> bool:
    """
    Returns True when the person is close enough for face recognition.
    Inverse of should_approach, but with the same threshold.
    """
    return not should_approach(bbox, frame_height)


def pick_largest_person(detections: list):
    """
    From a list of Detection namedtuples, return the one with
    the largest bounding box area (closest person).
    Returns None if list is empty.
    """
    if not detections:
        return None
    return max(detections, key=lambda d: (d.x2 - d.x1) * (d.y2 - d.y1))
