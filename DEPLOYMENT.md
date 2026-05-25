# 🚀 Raspberry Pi 5 — Hardware Deployment Guide

This guide details the exact steps to move the code from your development machine to the robot hardware and verify each system.

## 📂 1. File Structure on Raspberry Pi
Copy the entire `c7-smartrobo` folder to `/home/pi/`. It should look exactly like this:

```text
/home/pi/c7-smartrobo/
├── main.py                     # Entry point (run this)
├── config.py                   # Central settings
├── core/                       # FSM Engine
├── hardware/                   # Serial, motors, servo
├── vision/                     # Camera, YOLO, face_id, tracker
├── comms/                      # TTS, STT, Telegram, Ollama
├── data/                       # SQLite, Pickle DBs
├── behaviors/                  # Patrol, Approach, Interaction
├── known_faces/                # 📸 Put images of employees here
├── c7-robo-code-2/             # 🛠️ Arduino firmware
├── requirements.txt            # Python dependencies
├── en_US-lessac-medium.onnx    # Piper TTS model (MUST BE PRESENT)
└── yolov8n.pt                  # YOLO weights (Automatic download usually)
```

---

## 🛠️ 2. Raspberry Pi OS Configuration

### Enable Hardware UART (GPIO Serial)
Since you are using GPIO pins for communication (with your voltage divider):
1. Run: `sudo raspi-config`
2. Navigate to: **Interface Options > Serial Port**
3. **"Would you like a login shell over serial?"** → **NO**
4. **"Would you like the serial port hardware to be enabled?"** → **YES**
5. Reboot.

### Install System Dependencies
Run these commands on the Pi terminal:
```bash
sudo apt update
sudo apt install python3-pip python3-venv sox libatlas-base-dev -y
# SoX is required for the STT denoise pipeline
```

---

## 🐍 3. Software Installation
It is recommended to use a virtual environment:
```bash
cd ~/c7-smartrobo
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🤖 4. Arduino Setup
1. Open `c7-robo-code-2/c7-robo-code-2.ino` in the Arduino IDE.
2. Ensure you have the `Servo.h` library installed (standard).
3. Connect Arduino to Pi via USB (for flashing) or UART (if using Pi serial).
4. **Flash the code.**

---

## 🧪 5. Testing Sequence (The "Checklist")

Before running the full system, test components individually to ensure your wiring (UART/Voltage Divider) is correct.

### A. Test Serial & Motors
```bash
python -c "from hardware.motors import Motors; m = Motors(); m.forward(); import time; time.sleep(1); m.stop()"
```
*   **Success:** Robot moves forward for 1 second.

### B. Test Servo & Camera
```bash
python -c "from hardware.servo import Servo; s = Servo(); s.set_angle(0); import time; time.sleep(1); s.set_angle(180); time.sleep(1); s.center()"
```
*   **Success:** Camera pans left to right and centers.

### C. Test Voice (TTS)
```bash
python -c "from comms.tts import speak; speak('System online. UART connection verified.')"
```
*   **Success:** Voice heard through your speakers.

### D. Test Vision (YOLO)
```bash
python -c "from vision.camera import Camera; from vision.detector import PersonDetector; cam=Camera(); det=PersonDetector(); bgr, _ = cam.capture(); print(det.detect(bgr))"
```
*   **Success:** Prints a list of detections (stand in front of it!).

---

## 🚦 6. Running the System
Once all sub-tests pass:
```bash
python main.py
```
*   The robot will enter **PATROL** (Wait/Scan).
*   It will switch to **ROAMING** and move around.
*   Once a human is seen, it will **APPROACH** and initiate the **INTERACTION**.

> [!TIP]
> **Headless Mode:** If you aren't using a monitor on the Pi, go to `config.py` and set `DEBUG_DISPLAY = False`.
