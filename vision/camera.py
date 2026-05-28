"""
Camera Abstraction
══════════════════
Priority: Picamera2 (Raspberry Pi Camera) → USB webcam fallback.
Extracted from robot_merged.py lines 776–799.
"""

import cv2

try:
    from picamera2 import Picamera2
    _PICAMERA_AVAILABLE = True
except ImportError:
    _PICAMERA_AVAILABLE = False

import config


class Camera:
    """Unified camera interface — Picamera2 or USB webcam."""

    def __init__(self):
        self._picam = None
        self._cap = None
        self._use_picam = False

        if _PICAMERA_AVAILABLE:
            try:
                print("🔍 Checking for Raspberry Pi Camera...")
                self._picam = Picamera2()
                cam_config = self._picam.create_preview_configuration(
                    main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)}
                )
                self._picam.configure(cam_config)
                self._picam.start()
                self._use_picam = True
                print("✅ Raspberry Pi Camera detected and started.")
                return
            except Exception as e:
                print(f"⚠️  Picamera not available: {e}")
                self._picam = None

        # Fallback: USB webcam
        print("🔍 Falling back to USB webcam...")
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            raise RuntimeError(
                "❌ No camera found! Connect a webcam or enable the Pi Camera."
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        print("✅ USB webcam started.")

    def capture(self):
        """
        Capture a single frame.
        Returns (bgr_frame, rgb_frame) tuple, or (None, None) on failure.
        """
        if self._use_picam:
            frame = self._picam.capture_array()
            # Picamera2 formats might be 4-channel (XBGR or BGRA) depending on internal stream
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            else:
                rgb = frame
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return bgr, rgb

        ret, frame = self._cap.read()
        if not ret:
            return None, None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame, rgb

    def release(self):
        """Release camera resources."""
        if self._use_picam and self._picam is not None:
            self._picam.stop()
            print("📷 Picamera2 stopped.")
        if self._cap is not None:
            self._cap.release()
            print("📷 USB webcam released.")
