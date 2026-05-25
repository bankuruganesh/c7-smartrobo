"""
Approach Behavior — Center & Drive Toward Human
════════════════════════════════════════════════
Centers the detected person in frame using motor steering,
then drives forward until close enough for face recognition.
"""

import time
import config
from hardware.motors import Motors
from hardware.servo import Servo
from vision.detector import PersonDetector
from vision import human_tracker


class ApproachBehavior:
    """Steer toward and approach a detected human."""

    def __init__(self, motors: Motors, servo: Servo, detector: PersonDetector):
        self._motors = motors
        self._servo = servo
        self._detector = detector
        self._lost_frames = 0

    def reset(self):
        """Reset lost-frame counter (call on APPROACH enter)."""
        self._lost_frames = 0
        self._servo.center()

    def step(self, bgr_frame, frame_width: int, frame_height: int) -> str:
        """
        Perform one approach step.

        Parameters
        ----------
        bgr_frame    : current camera frame (BGR)
        frame_width  : int
        frame_height : int

        Returns
        -------
        "APPROACHING"   – still moving toward human
        "CLOSE_ENOUGH"  – within face-recognition distance
        "LOST"          – human lost for too many frames
        """
        detections = self._detector.detect(bgr_frame)
        person = human_tracker.pick_largest_person(detections)

        if person is None:
            self._lost_frames += 1
            if self._lost_frames >= config.APPROACH_LOST_FRAMES:
                self._motors.stop()
                print("  ❌ Human lost — aborting approach.")
                return "LOST"
            # Keep last motor command briefly
            return "APPROACHING"

        self._lost_frames = 0

        # ── Check if close enough ─────────────────────────────
        if human_tracker.is_close_enough(person, frame_height):
            self._motors.stop()
            print("  ✅ Close enough for face recognition.")
            return "CLOSE_ENOUGH"

        # ── Steer to center the person ────────────────────────
        direction, offset = human_tracker.compute_steering(person, frame_width)

        if direction == "LEFT":
            self._motors.left()
            time.sleep(config.APPROACH_TURN_DURATION)
            self._motors.stop()
        elif direction == "RIGHT":
            self._motors.right()
            time.sleep(config.APPROACH_TURN_DURATION)
            self._motors.stop()

        # ── Drive forward if centered ─────────────────────────
        if direction == "CENTER":
            self._motors.forward()

        return "APPROACHING"

    def get_current_person(self, bgr_frame):
        """Get the largest person detection from current frame."""
        detections = self._detector.detect(bgr_frame)
        return human_tracker.pick_largest_person(detections)
