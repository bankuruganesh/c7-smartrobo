"""
Patrol Behavior — Scan & Roam
═════════════════════════════
1. SCAN: Sweep servo looking for humans.
   If human found → return True (caller transitions to APPROACH).
2. ROAM: Drive forward with obstacle avoidance, periodically re-scan.
"""

import time
import config
from hardware.motors import Motors
from hardware.servo import Servo
from vision.detector import PersonDetector
from vision.human_tracker import pick_largest_person


class PatrolBehavior:
    """Encapsulates patrol scanning and roaming logic."""

    def __init__(self, motors: Motors, servo: Servo, detector: PersonDetector):
        self._motors = motors
        self._servo = servo
        self._detector = detector
        self._last_scan_time = 0.0

    # ── SCAN ──────────────────────────────────────────────────
    def scan(self, capture_func) -> bool:
        """
        Perform a full servo sweep, checking for humans at each position.

        Parameters
        ----------
        capture_func : callable → returns (bgr_frame, rgb_frame)

        Returns
        -------
        True if a human was detected during the sweep.
        """
        self._motors.stop()

        def _check_at_angle(angle):
            """Callback for servo.scan_sweep — returns True if person found."""
            bgr, _ = capture_func()
            if bgr is None:
                return False
            detections = self._detector.detect(bgr)
            person = pick_largest_person(detections)
            if person is not None:
                print(f"  👁️ Person detected at servo angle {angle}°!")
                return True
            return False

        print("🔍 Scanning environment...")
        found = self._servo.scan_sweep(callback=_check_at_angle)
        self._last_scan_time = time.time()
        return found

    # ── ROAM ──────────────────────────────────────────────────
    def roam_step(self, capture_func) -> bool:
        """
        Perform one roam step: drive forward, avoid obstacles.
        Checks for humans while roaming.

        Parameters
        ----------
        capture_func : callable → returns (bgr_frame, rgb_frame)

        Returns
        -------
        True if a human was detected (caller should transition to APPROACH).
        """
        # Check for humans in current frame first
        bgr, _ = capture_func()
        if bgr is not None:
            detections = self._detector.detect(bgr)
            person = pick_largest_person(detections)
            if person is not None:
                self._motors.stop()
                print("  👁️ Person detected during roam!")
                return True

        # Obstacle avoidance
        distance = self._motors.get_distance()

        if 0 < distance < config.OBSTACLE_THRESHOLD_CM:
            print(f"  🚧 Obstacle at {distance}cm — turning...")
            self._motors.stop()
            time.sleep(0.1)
            self._motors.timed_turn("R", 0.6)
        else:
            self._motors.forward()

        return False

    def should_rescan(self) -> bool:
        """Returns True if enough time has passed for a new servo sweep."""
        return (time.time() - self._last_scan_time) > config.ROAM_RESCAN_INTERVAL
