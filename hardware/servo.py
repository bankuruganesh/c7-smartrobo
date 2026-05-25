"""
Servo Camera Pan Controller
════════════════════════════
Controls the servo motor that pans the camera via Arduino.
Uses the new P<angle> serial command.
"""

import time
import config
from hardware.serial_comm import ArduinoSerial


class Servo:
    """Servo motor control for camera panning."""

    def __init__(self):
        self._serial = ArduinoSerial()
        self._current_angle = config.SERVO_CENTER

    @property
    def angle(self) -> int:
        return self._current_angle

    def set_angle(self, degrees: int):
        """Set servo to a specific angle (0–180)."""
        degrees = max(config.SERVO_MIN, min(config.SERVO_MAX, degrees))
        self._serial.send(f"P{degrees}")
        self._current_angle = degrees

    def center(self):
        """Return servo to center position (90°)."""
        self.set_angle(config.SERVO_CENTER)

    def scan_sweep(self, callback=None) -> bool:
        """
        Sweep the servo from SERVO_MIN to SERVO_MAX in steps.
        At each position, pauses and calls callback(angle).
        If callback returns True, the sweep stops early (human found).
        Returns True if callback signalled early-stop, False if full sweep completed.
        """
        step = config.SERVO_SCAN_STEP
        angles = list(range(config.SERVO_MIN, config.SERVO_MAX + 1, step))

        # Alternate sweep direction for more natural scanning
        for angle in angles:
            self.set_angle(angle)
            time.sleep(config.SERVO_STEP_DELAY)

            if callback is not None:
                if callback(angle):
                    return True     # human found, stop sweep

        # Return to center after sweep
        self.center()
        return False
