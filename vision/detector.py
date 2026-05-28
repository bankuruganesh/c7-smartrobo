"""
YOLO Person Detector
════════════════════
Wraps YOLOv8n with frame-skipping to reduce CPU load.
Extracted from robot_merged.py with added caching logic.
"""

from collections import namedtuple
from ultralytics import YOLO
import config

Detection = namedtuple("Detection", ["x1", "y1", "x2", "y2", "confidence"])


class PersonDetector:
    """Person detection using YOLOv8n with frame-skip caching."""

    def __init__(self):
        print("🔍 Loading YOLO model...")
        self._model = YOLO(config.YOLO_MODEL_PATH)
        self._skip = config.YOLO_SKIP_FRAMES
        self._cached = []
        self._frame_count = 0
        print("✅ YOLO loaded.")

    def detect(self, bgr_frame) -> list[Detection]:
        """
        Run person detection.
        Only runs YOLO every N frames; returns cached results otherwise.
        Returns list of Detection namedtuples for class 0 (person).
        """
        self._frame_count += 1

        if self._frame_count % self._skip != 0:
            return self._cached

        # Run YOLO
        results = self._model(
            bgr_frame,
            verbose=False,
            imgsz=config.YOLO_IMGSZ,
            half=False,
        )

        detections = []
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) != 0:   # class 0 = person
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                detections.append(Detection(x1, y1, x2, y2, conf))

        self._cached = detections
        return detections

    def reset(self):
        """Clear cached detections (e.g., after state transition)."""
        self._cached = []
        self._frame_count = 0
