"""
C7 Smart Patrol Robot — Central Configuration
═══════════════════════════════════════════════
All tuneable constants in one place.
Nothing else in the project should hard-code values.
"""

import os

# ─── Telegram ────────────────────────────────────────────────
TELEGRAM_TOKEN = "8310932356:AAGfJ3SekJRxTI4jAXU_ppuKa9b7cvEb64Y"

USER_CHAT_IDS = {
    "ravi":   "5790709597",
    "lokesh": "5978530879",
    "tarun":  "6663176931",
    "sairam": "8171470054",
    "ganesh": "5693255882",
}

KNOWN_EMPLOYEES = list(USER_CHAT_IDS.keys())

# ─── Face Recognition ───────────────────────────────────────
FACE_TOLERANCE   = 0.52
REQUIRED_FRAMES  = 8          # consistent detections before trigger
UNKNOWN_COOLDOWN = 300        # seconds before re-engaging same unknown

# ─── File Paths ──────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
VISITORS_DIR     = os.path.join(BASE_DIR, "visitors")
FACES_DB_PATH    = os.path.join(BASE_DIR, "faces_db.pkl")
VISITORS_DB_PATH = os.path.join(BASE_DIR, "visitors_db.pkl")
SQLITE_DB_PATH   = os.path.join(BASE_DIR, "visitors.db")

os.makedirs(VISITORS_DIR, exist_ok=True)

# ─── Serial / Arduino ───────────────────────────────────────
#  Hardware UART via GPIO pins (voltage divider on Pi RX ← Arduino TX)
SERIAL_PORT      = "/dev/serial0"
SERIAL_BAUD      = 9600
SERIAL_TIMEOUT   = 0.1        # read timeout in seconds

# ─── YOLO ────────────────────────────────────────────────────
YOLO_MODEL_PATH  = "yolov8n.pt"
YOLO_IMGSZ       = 320
YOLO_SKIP_FRAMES = 3          # run YOLO every Nth frame

# ─── Camera ──────────────────────────────────────────────────
CAMERA_WIDTH     = 640
CAMERA_HEIGHT    = 480

# ─── Servo (camera pan) ─────────────────────────────────────
SERVO_PIN        = 10         # Arduino digital pin
SERVO_CENTER     = 90
SERVO_MIN        = 0
SERVO_MAX        = 180
SERVO_SCAN_STEP  = 30         # degrees per scan step
SERVO_STEP_DELAY = 0.8        # seconds to wait at each scan position

# ─── Human Approach ──────────────────────────────────────────
#  Thresholds for the approach behavior
APPROACH_CENTER_TOLERANCE = 60   # pixels from frame center → considered centered
APPROACH_CLOSE_RATIO      = 0.38 # bbox height / frame height → close enough to stop
APPROACH_LOST_FRAMES      = 15   # frames without person → abort approach
APPROACH_TURN_DURATION    = 0.25 # seconds per steering correction

# ─── TTS (Piper) ─────────────────────────────────────────────
PIPER_MODEL      = os.path.join(BASE_DIR, "en_US-lessac-medium.onnx")
PIPER_OUTPUT     = os.path.join(BASE_DIR, "piper_output.wav")
PIPER_LENGTH_SCALE = "1.3"

# ─── STT (Faster-Whisper) ────────────────────────────────────
WHISPER_MODEL_SIZE   = "small.en"
WHISPER_DEVICE       = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
STT_SAMPLE_RATE      = 16000
STT_RECORD_SECONDS   = 5
STT_MAX_FAILS        = 2      # consecutive failures before abort

# ─── LLM (Ollama) ────────────────────────────────────────────
OLLAMA_MODEL = "gemma3:1b"

# ─── Obstacle Avoidance ──────────────────────────────────────
OBSTACLE_THRESHOLD_CM = 30    # matches Arduino's obstacleThreshold

# ─── Patrol Roam ─────────────────────────────────────────────
ROAM_FORWARD_SECONDS  = 2.0   # how long to drive forward between scans
ROAM_RESCAN_INTERVAL  = 8.0   # seconds between full servo sweeps while roaming

# ─── Debug ───────────────────────────────────────────────────
DEBUG_DISPLAY = True           # show cv2 window with bounding boxes
