"""
Arduino Serial Communication
═════════════════════════════
Hardware UART connection via GPIO pins (Pi TX → Arduino RX direct,
Arduino TX → voltage divider → Pi RX).

Port: /dev/ttyAMA0   Baud: 9600

Thread-safe singleton — all modules share one instance.
"""

import serial
import threading
import time
import config


class ArduinoSerial:
    """Thread-safe serial wrapper for the Arduino."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton — only one serial connection to the Arduino."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self):
        if self._initialised:
            return
        self._initialised = True
        self._serial = None
        self._rw_lock = threading.Lock()
        self._connect()

    # ── Connection ────────────────────────────────────────────
    def _connect(self):
        """Open the serial port.  Retries once on failure."""
        try:
            self._serial = serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.SERIAL_BAUD,
                timeout=config.SERIAL_TIMEOUT,
            )
            # Flush any stale data
            time.sleep(0.1)
            self._serial.reset_input_buffer()
            print(f"✅ Arduino serial connected on {config.SERIAL_PORT}")
        except serial.SerialException as e:
            print(f"❌ Arduino serial FAILED: {e}")
            self._serial = None

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def reconnect(self):
        """Close and re-open the serial port."""
        self.close()
        time.sleep(0.5)
        self._connect()

    # ── Send ──────────────────────────────────────────────────
    def send(self, cmd: str):
        """
        Send a command string to the Arduino.
        Appends '\\n' automatically.
        """
        if not self.connected:
            print("⚠️  Serial not connected — cannot send")
            return
        with self._rw_lock:
            try:
                self._serial.write(f"{cmd}\n".encode())
                self._serial.flush()
            except serial.SerialException as e:
                print(f"⚠️  Serial write error: {e}")
                self.reconnect()

    # ── Read ──────────────────────────────────────────────────
    def read_line(self, timeout: float = 0.5) -> str | None:
        """
        Read one line from Arduino (blocking up to *timeout* seconds).
        Returns the decoded, stripped string or None.
        """
        if not self.connected:
            return None
        with self._rw_lock:
            old_timeout = self._serial.timeout
            self._serial.timeout = timeout
            try:
                raw = self._serial.readline()
                if raw:
                    return raw.decode("utf-8", errors="ignore").strip()
            except serial.SerialException as e:
                print(f"⚠️  Serial read error: {e}")
                self.reconnect()
            finally:
                self._serial.timeout = old_timeout
        return None

    # ── Convenience ───────────────────────────────────────────
    def get_distance(self) -> int:
        """
        Send 'U' (ultrasonic), parse 'DIST:<cm>' response.
        Returns distance in cm, or -1 on error.
        """
        self.send("U")
        
        # Arduino echoes "Received: U" before sending "DIST:X", so we might need
        # to read a couple of lines before hitting the actual target.
        start_time = time.time()
        while time.time() - start_time < 0.5:
            line = self.read_line(timeout=0.1)
            if not line:
                continue
            if line.startswith("DIST:"):
                try:
                    return int(line.split(":")[1])
                except (ValueError, IndexError):
                    pass
        return -1

    # ── Cleanup ───────────────────────────────────────────────
    def close(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("🔌 Arduino serial closed.")
