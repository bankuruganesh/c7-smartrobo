"""
C7 Smart Patrol Robot — Main Orchestrator
══════════════════════════════════════════
Boots all modules, creates the FSM, and runs the main loop.

Usage:  python main.py

Flow:
    PATROL → SCAN (servo sweep) → ROAM (obstacle avoidance)
    → APPROACH (detected human) → IDENTIFY (face recognition)
    → INTERACT (greet / conversation / telegram) → PATROL
"""

import time
import cv2
import signal
import sys

# ── Project Modules ──────────────────────────────────────────
import config
from core.fsm import FSM
from hardware.serial_comm import ArduinoSerial
from hardware.motors import Motors
from hardware.servo import Servo
from vision.camera import Camera
from vision.detector import PersonDetector
from vision import human_tracker
from behaviors.patrol import PatrolBehavior
from behaviors.approach import ApproachBehavior
from behaviors.interaction import InteractionBehavior
from comms import tts
from data.database import init_db


# ═════════════════════════════════════════════════════════════
#  GRACEFUL SHUTDOWN
# ═════════════════════════════════════════════════════════════

_running = True


def _shutdown(signum=None, frame=None):
    global _running
    _running = False
    print("\n🛑 Shutdown signal received...")


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


# ═════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════

def main():
    global _running

    print("═" * 60)
    print("  C7 Smart Patrol Robot — Booting")
    print("═" * 60)

    # ── 0. Initialize Database ────────────────────────────────
    init_db()

    # ── 1. Initialise Hardware ────────────────────────────────
    serial_conn = ArduinoSerial()
    motors = Motors()
    servo  = Servo()
    camera = Camera()

    # ── 2. Initialise Vision ──────────────────────────────────
    detector = PersonDetector()

    # ── 3. Initialise Behaviors ───────────────────────────────
    patrol_beh      = PatrolBehavior(motors, servo, detector)
    approach_beh    = ApproachBehavior(motors, servo, detector)
    interaction_beh = InteractionBehavior()

    # ── 4. Initialise FSM ─────────────────────────────────────
    fsm = FSM()

    # Register enter/exit hooks
    fsm.on_enter(FSM.APPROACH, approach_beh.reset)
    fsm.on_enter(FSM.PATROL, lambda: motors.stop())

    # ── 5. Initial State ──────────────────────────────────────
    motors.stop()
    servo.center()
    time.sleep(0.5)

    # Counters for IDENTIFY state (stable detection before interaction)
    person_det_frames = 0

    print("\n🚀 Smart Robot — PATROL mode active.  Press Q to quit.\n")

    # ═════════════════════════════════════════════════════════
    #  MAIN LOOP
    # ═════════════════════════════════════════════════════════

    while _running:
        bgr_frame, rgb_frame = camera.capture()
        if bgr_frame is None:
            print("❌ Failed to capture frame.")
            time.sleep(0.1)
            continue

        h, w = bgr_frame.shape[:2]

        # ─────────────────────────────────────────────────────
        #  STATE: PATROL → transition to SCAN
        # ─────────────────────────────────────────────────────
        if fsm.is_state(FSM.PATROL):
            fsm.transition(FSM.SCAN)

        # ─────────────────────────────────────────────────────
        #  STATE: SCAN — servo sweep looking for humans
        # ─────────────────────────────────────────────────────
        elif fsm.is_state(FSM.SCAN):
            found = patrol_beh.scan(camera.capture)
            if found:
                servo.center()
                fsm.transition(FSM.APPROACH)
            else:
                fsm.transition(FSM.ROAM)

        # ─────────────────────────────────────────────────────
        #  STATE: ROAM — drive forward, avoid obstacles
        # ─────────────────────────────────────────────────────
        elif fsm.is_state(FSM.ROAM):
            human_found = patrol_beh.roam_step(camera.capture)
            if human_found:
                fsm.transition(FSM.APPROACH)
            elif patrol_beh.should_rescan():
                motors.stop()
                fsm.transition(FSM.SCAN)

        # ─────────────────────────────────────────────────────
        #  STATE: APPROACH — center and drive toward human
        # ─────────────────────────────────────────────────────
        elif fsm.is_state(FSM.APPROACH):
            result = approach_beh.step(bgr_frame, w, h)

            if result == "CLOSE_ENOUGH":
                person_det_frames = 0
                fsm.transition(FSM.IDENTIFY)
            elif result == "LOST":
                fsm.transition(FSM.PATROL)
            # else "APPROACHING" — continue

        # ─────────────────────────────────────────────────────
        #  STATE: IDENTIFY — stable face detection
        # ─────────────────────────────────────────────────────
        elif fsm.is_state(FSM.IDENTIFY):
            # Wait for REQUIRED_FRAMES consistent person detections
            detections = detector.detect(bgr_frame)
            person = human_tracker.pick_largest_person(detections)

            if person is not None:
                person_det_frames += 1
            else:
                person_det_frames = max(0, person_det_frames - 1)

            if person_det_frames >= config.REQUIRED_FRAMES:
                person_det_frames = 0
                fsm.transition(FSM.INTERACT)
            elif person_det_frames == 0 and fsm.time_in_state > 3.0:
                # Lost the person during identification
                fsm.transition(FSM.PATROL)

        # ─────────────────────────────────────────────────────
        #  STATE: INTERACT — face recognition + conversation
        # ─────────────────────────────────────────────────────
        elif fsm.is_state(FSM.INTERACT):
            motors.stop()

            # Get the current person detection for face analysis
            detections = detector.detect(bgr_frame)
            person = human_tracker.pick_largest_person(detections)

            if person is not None:
                result = interaction_beh.handle_face(
                    bgr_frame, rgb_frame, person
                )
                print(f"  ✅ Interaction result: {result}")
            else:
                print("  ℹ️ Person lost before interaction could start.")

            fsm.force(FSM.PATROL)

        # ─────────────────────────────────────────────────────
        #  DEBUG DISPLAY
        # ─────────────────────────────────────────────────────
        if config.DEBUG_DISPLAY:
            # Draw detections
            detections = detector.detect(bgr_frame)
            for det in detections:
                cv2.rectangle(
                    bgr_frame,
                    (det.x1, det.y1), (det.x2, det.y2),
                    (255, 0, 0), 2,
                )
                cv2.putText(
                    bgr_frame, "Person",
                    (det.x1, det.y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2,
                )

            # State overlay
            cv2.putText(
                bgr_frame, f"State: {fsm.state}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 220), 2,
            )
            try:
                cv2.imshow("Smart Robot", bgr_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
            except Exception as e:
                print(f"⚠️ Display error (headless mode?): {e}")
                config.DEBUG_DISPLAY = False

        # Small delay to avoid CPU spinning
        time.sleep(0.02)

    # ═════════════════════════════════════════════════════════
    #  CLEANUP
    # ═════════════════════════════════════════════════════════
    print("\n🧹 Cleaning up...")
    motors.stop()
    servo.center()
    camera.release()
    serial_conn.close()
    tts.cleanup()
    cv2.destroyAllWindows()
    print("👋 Robot shutdown complete.\n")


if __name__ == "__main__":
    main()
