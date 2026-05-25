"""
Motor Control Abstraction
═════════════════════════
High-level motor commands that delegate to Arduino via serial.
Matches the existing Arduino protocol: F, B, L, R, S
"""

import time
import threading
from hardware.serial_comm import ArduinoSerial


class Motors:
    """Stateful motor controller with debounce."""

    def __init__(self):
        self._serial = ArduinoSerial()
        self._last_cmd = None
        self._last_time = 0.0
        self._debounce = 0.05   # 50 ms

    def _send(self, cmd: str):
        """Send command with debounce — ignores duplicates within 50 ms."""
        now = time.time()
        if cmd == self._last_cmd and (now - self._last_time) < self._debounce:
            return
        self._serial.send(cmd)
        self._last_cmd = cmd
        self._last_time = now

    # ── Basic Commands ────────────────────────────────────────
    def forward(self):
        self._send("F")

    def backward(self):
        self._send("B")

    def left(self):
        self._send("L")

    def right(self):
        self._send("R")

    def stop(self):
        self._send("S")
        self._last_cmd = None   # always allow stop

    # ── Timed Commands ────────────────────────────────────────
    def timed_forward(self, seconds: float):
        """Drive forward for *seconds*, then stop.  Blocking."""
        self.forward()
        time.sleep(seconds)
        self.stop()

    def timed_turn(self, direction: str, seconds: float):
        """
        Turn left or right for *seconds*, then stop.  Blocking.
        direction: 'L' or 'R'
        """
        if direction == "L":
            self.left()
        elif direction == "R":
            self.right()
        time.sleep(seconds)
        self.stop()

    # ── Speed Control ─────────────────────────────────────────
    def set_speed(self, value: int):
        """Set motor PWM speed (0-255) via the V<speed> command."""
        value = max(0, min(255, value))
        self._serial.send(f"V{value}")

    # ── Autonomous Kick ───────────────────────────────────────
    def autonomous_step(self):
        """Send 'A' — Arduino handles one obstacle-avoidance step."""
        self._serial.send("A")

    # ── Distance Query ────────────────────────────────────────
    def get_distance(self) -> int:
        """Get ultrasonic distance in cm (-1 on error)."""
        return self._serial.get_distance()
