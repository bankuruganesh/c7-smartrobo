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

## 🛠️ 7. Troubleshooting (If Hardware doesn't move)

If the script says `✅ Arduino serial connected` but the robot doesn't move:

### A. Common Ground (Most Important!)
The Raspberry Pi and the Arduino **MUST share a common Ground (GND)**.
*   Connect any **GND** pin on the Pi (e.g., Pin 6, 9, 14, 20, or 25) to a **GND** pin on the Arduino.
*   Without this, the electrical signals have no reference point and will be ignored.

### B. Serial Console Conflict
The Pi's internal Linux system might be using the same UART pins for a "Login Shell".
1.  Run `ls -l /dev/serial0` (it should point to `ttyAMA0` or `ttyS0`).
2.  Open `/boot/firmware/cmdline.txt` (or `/boot/cmdline.txt`).
3.  **Remove** any part that says `console=serial0,115000` or `console=ttyAMA0,115000`.
4.  Reboot.

### C. Pin Swap
Double check your TX/RX wiring:
*   **Pi TX (GPIO 14 / Pin 8)** → **Arduino RX (Pin 0)**
*   **Pi RX (GPIO 15 / Pin 10)** ← **Voltage Divider** ← **Arduino TX (Pin 1)**

### D. Verify with Diagnostic Script
Run this tool I created to find the working port:
```bash
python diag_serial.py
```
If it says `SUCCESS!`, copy the port name into `config.py` under `SERIAL_PORT`.

### E. Power
Ensure the Arduino has enough power to drive the motors. If the Arduino is powered only by the Pi's 5V pin, it might reboot when motors draw current. Use a battery or a separate 5V regulator for the motors.

