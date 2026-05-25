"""
Interaction Behavior — Greet, Converse, Telegram, Log
═════════════════════════════════════════════════════
Handles the full interaction pipeline once a face is identified:
- Permanent staff → quick greeting
- Returning visitor → conversation + Telegram
- Unknown visitor → conversation + register face + Telegram
"""

import time
import os
import cv2
import config
from comms.tts import speak
from comms.conversation import visitor_conversation
from comms.stt import ConversationAborted
from comms import telegram_bot, llm
from data.database import save_log
from data.face_db import FaceDB
from vision.face_id import identify, detect_faces_in_roi, get_unknown_fingerprint


class InteractionBehavior:
    """Manages all human interaction states."""

    def __init__(self):
        self._greeted_permanent = set()
        self._greeted_visitors  = set()
        self._unknown_cooldowns = []    # [(encoding, timestamp), ...]
        self._face_db = FaceDB()

    def reset_session(self):
        """Clear greeted sets (e.g., new patrol session)."""
        self._greeted_permanent.clear()
        self._greeted_visitors.clear()

    # ── Main Entry Point ──────────────────────────────────────
    def handle_face(self, bgr_frame, rgb_frame, person_bbox) -> str:
        """
        Run face recognition on the detected person and handle interaction.

        Parameters
        ----------
        bgr_frame  : BGR frame for image saving
        rgb_frame  : RGB frame for face_recognition
        person_bbox: Detection namedtuple (x1, y1, x2, y2, confidence)

        Returns
        -------
        "DONE"     — interaction complete, resume patrol
        "ABORTED"  — conversation aborted (STT failures)
        "SKIPPED"  — already greeted or on cooldown
        """
        # Extract person ROI and find faces
        x1, y1, x2, y2 = person_bbox.x1, person_bbox.y1, person_bbox.x2, person_bbox.y2
        person_roi = bgr_frame[y1:y2, x1:x2]
        if person_roi.size == 0:
            return "SKIPPED"

        roi_rgb = cv2.cvtColor(person_roi, cv2.COLOR_BGR2RGB)
        face_locations = detect_faces_in_roi(roi_rgb)

        if not face_locations:
            print("  ℹ️ Person detected but no face visible.")
            return "SKIPPED"

        # Use the first (largest) face
        top, right, bottom, left = face_locations[0]

        # Skip tiny faces (likely false positives)
        if (right - left) < 80:
            return "SKIPPED"

        # Map ROI coordinates → full-frame coordinates
        abs_top    = y1 + top
        abs_right  = x1 + right
        abs_bottom = y1 + bottom
        abs_left   = x1 + left
        face_loc   = (abs_top, abs_right, abs_bottom, abs_left)

        # Identify the face
        name, category, encoding = identify(rgb_frame, face_loc)

        try:
            if category == "permanent":
                return self._handle_permanent(name)
            elif category == "visitor":
                return self._handle_visitor(name, bgr_frame)
            else:
                return self._handle_unknown(name, encoding, bgr_frame)

        except ConversationAborted:
            print("  ⚠️ Conversation aborted (STT fails). Resuming patrol.")
            # Allow re-engagement next time
            self._greeted_permanent.discard(name)
            self._greeted_visitors.discard(name)
            return "ABORTED"

    # ── Permanent Staff ───────────────────────────────────────
    def _handle_permanent(self, name: str) -> str:
        if name in self._greeted_permanent:
            print(f"  ℹ️ {name} already greeted this session.")
            return "SKIPPED"

        speak(f"Hello {name}! Welcome back. Have a great day!")
        self._greeted_permanent.add(name)
        return "DONE"

    # ── Returning Visitor ─────────────────────────────────────
    def _handle_visitor(self, name: str, bgr_frame) -> str:
        if name in self._greeted_visitors:
            print(f"  ℹ️ {name} already handled this session.")
            return "SKIPPED"

        visitor_info = visitor_conversation(known_name=name)
        self._handle_purpose_flow(bgr_frame, visitor_info)
        self._greeted_visitors.add(name)
        return "DONE"

    # ── Unknown / First-Time ──────────────────────────────────
    def _handle_unknown(self, name: str, encoding, bgr_frame) -> str:
        now = time.time()
        cooldown_idx = None

        if encoding is not None:
            cooldown_idx = get_unknown_fingerprint(
                encoding, self._unknown_cooldowns
            )

        if cooldown_idx is not None:
            _, last_time = self._unknown_cooldowns[cooldown_idx]
            remaining = config.UNKNOWN_COOLDOWN - (now - last_time)
            if remaining > 0:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                print(f"  ⏳ Cooldown: {mins}m {secs}s remaining — skipping.")
                return "SKIPPED"
            else:
                self._unknown_cooldowns[cooldown_idx] = (encoding, now)
                print("  ✅ Cooldown expired. Re-engaging.")
        else:
            if encoding is not None:
                self._unknown_cooldowns.append((encoding, now))
            print("  🆕 First-time unknown visitor.")

        visitor_info = visitor_conversation(known_name=None)
        visitor_name = visitor_info["name"]
        speak(f"Nice to meet you, {visitor_name}!")
        self._handle_purpose_flow(bgr_frame, visitor_info)

        if encoding is not None:
            self._face_db.register_visitor(encoding, visitor_name)

        return "DONE"

    # ── Purpose Flow (Telegram) ───────────────────────────────
    def _handle_purpose_flow(self, bgr_frame, visitor_info: dict):
        """Send Telegram alert, wait for decision, log everything."""
        name    = visitor_info["name"]
        person  = visitor_info["person"]
        purpose = visitor_info["purpose"]

        image_path = self._save_visitor_image(bgr_frame, name)
        matched = llm.match_person(person)

        if matched:
            chat_id = config.USER_CHAT_IDS[matched]
            speak(
                f"Thank you, {name}. I am notifying {matched.capitalize()} right now. "
                "Please wait a moment."
            )
            telegram_bot.send_alert(image_path, name, purpose, chat_id)
            decision = telegram_bot.wait_for_decision(chat_id, timeout=60)

            # Speak decision
            if decision == "admit":
                speak("Great news! You have been approved to go in. Please proceed.")
            elif decision == "wait":
                speak("The person will be with you shortly. Please have a seat and wait.")
            elif decision == "busy":
                speak(
                    "I'm sorry, the person is currently busy. "
                    "Please try again later or leave a message at the front desk."
                )
            else:
                speak(
                    "I'm sorry, there was no response from the employee. "
                    "Please check with the front desk or try again in a few minutes."
                )
        else:
            speak(
                f"I'm sorry, I couldn't find '{person}' in our system. "
                "Please double-check the name or speak to the front desk."
            )
            decision = "person_not_found"
            matched  = person

        save_log(
            name=name,
            purpose=purpose,
            person=matched or "unknown",
            decision=decision,
            image_path=image_path,
        )

    # ── Image Save ────────────────────────────────────────────
    @staticmethod
    def _save_visitor_image(bgr_frame, name: str) -> str:
        person_dir = os.path.join(config.VISITORS_DIR, name)
        os.makedirs(person_dir, exist_ok=True)
        path = os.path.join(person_dir, f"{name}_{int(time.time())}.jpg")
        cv2.imwrite(path, bgr_frame)
        print(f"  📸 Visitor image saved: {path}")
        return path
