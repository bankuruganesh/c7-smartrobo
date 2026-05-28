# Changelog

All notable changes to the C7 Smart Patrol Robot project will be documented in this file.

## [2026-05-28 11:56:00] - Hardware Audit & Configuration Fixes

### Added
- Created `diag_serial.py`: A utility script to test two-way UART communication and diagnose hardware issues.
- Added comprehensive UART troubleshooting steps to `DEPLOYMENT.md` (Common ground, Pi 5 serial console conflicts).

### Fixed / Changed
**Configuration & Global**
- `config.py`: Updated hardware UART mapping to use `/dev/ttyAMA0` and `SERIAL_TIMEOUT` to 1.0s based on successful hardware testing.
- `main.py`: Added early execution of SQLite `init_db()` at boot sequence to prevent race conditions.
- `main.py`: Wrapped `cv2.imshow()` in a `try/except` block to prevent the main loop from crashing if executed via headless SSH.

**Hardware Interfaces**
- `hardware/serial_comm.py`: Fixed `get_distance()` bug. Python now cleanly processes multiple lines until it hits `DIST:x`, ignoring the debug `Received: U` echoes from the Arduino.
- `c7-robo-code-2.ino`: Fully updated Arduino sketch to match the robust `readStringUntil('\n')` parsing capability provided by the user.

**Vision & Artificial Intelligence**
- `vision/detector.py`: Disabled `half=True` in the YOLO initialization. The Raspberry Pi 5 CPU does not support FP16 operation natively; keeping it False prevents a fatal `RuntimeError`.
- `vision/camera.py`: Modified `capture()` logic to flexibly handle raw 4-channel BGRA/XBGR streams from Picamera2, enforcing strict 3-channel BGR and RGB to prevent logic failures in the `face_recognition` library.

**Communication & Behaviors**
- `comms/stt.py`: Changed Faster-Whisper temporary WAV file paths to use absolute addresses (via `config.BASE_DIR`) instead of relative paths.
- `comms/telegram_bot.py`: Added a 5-second connection timeout to `drain_updates()` at module import stage to prevent the robot from hanging on boot if the WiFi network is temporarily down.
- `behaviors/patrol.py`: Optimized ultrasonic distance checks during the `ROAM` state to only poll every 0.4 seconds, preventing the slower serial UART from degrading the visual frame rate.
