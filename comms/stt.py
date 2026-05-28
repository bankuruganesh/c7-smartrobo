"""
Speech-to-Text — Faster-Whisper + SoX
══════════════════════════════════════
Offline STT using sounddevice recording → SoX denoise → Whisper.
Extracted from robot_merged.py lines 277–401.
"""

import subprocess
import os
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from faster_whisper import WhisperModel
import config


class ConversationAborted(Exception):
    """Raised after STT_MAX_FAILS consecutive failures."""
    pass


# ── Model Load (once at import) ──────────────────────────────
print("🎙️ Loading Faster-Whisper model...")

_whisper = WhisperModel(
    config.WHISPER_MODEL_SIZE,
    device=config.WHISPER_DEVICE,
    compute_type=config.WHISPER_COMPUTE_TYPE,
)

print("✅ Faster-Whisper loaded.")

# ── Fail Counter ──────────────────────────────────────────────
_fail_count = 0


def reset_fail_counter():
    """Call at the start of every new conversation."""
    global _fail_count
    _fail_count = 0


def listen() -> str:
    """
    Record from microphone, denoise, transcribe.

    Returns the transcribed text.
    Raises ConversationAborted after STT_MAX_FAILS consecutive failures.
    On first failure, asks user to repeat and retries recursively.
    """
    global _fail_count

    try:
        print("  🎤 Listening...")

        audio = sd.rec(
            int(config.STT_RECORD_SECONDS * config.STT_SAMPLE_RATE),
            samplerate=config.STT_SAMPLE_RATE,
            channels=1,
            dtype=np.int16,
        )
        sd.wait()

        raw_path   = os.path.join(config.BASE_DIR, "temp_audio.wav")
        clean_path = os.path.join(config.BASE_DIR, "clean_audio.wav")

        # Save raw mic audio
        wav_write(raw_path, config.STT_SAMPLE_RATE, audio)

        # SoX denoise + cleanup
        subprocess.run(
            [
                "sox", raw_path, clean_path,
                "highpass", "80",
                "lowpass", "7000",
                "norm",
            ],
            check=True,
        )

        # Whisper STT
        segments, _ = _whisper.transcribe(
            clean_path,
            beam_size=3,
            initial_prompt=(
                "Possible names are Lokesh, Ravi, Tarun, "
                "Sairam, Ganesh."
            ),
        )

        text = "".join(seg.text for seg in segments).strip()

        # Cleanup temp files
        for p in (raw_path, clean_path):
            if os.path.exists(p):
                os.remove(p)

        if not text:
            raise ValueError("Empty transcription")

        print(f"  Visitor: {text}")
        _fail_count = 0
        return text

    except Exception as e:
        _fail_count += 1
        print(f"  STT fail {_fail_count}/{config.STT_MAX_FAILS} — {e}")

        if _fail_count >= config.STT_MAX_FAILS:
            _fail_count = 0

            # Import here to avoid circular dependency
            from comms.tts import speak
            speak(
                "I'm having trouble hearing you. "
                "I'll step back for now — "
                "please approach me again when you're ready."
            )
            raise ConversationAborted("STT failed twice")

        from comms.tts import speak
        speak(
            "Sorry, I didn't quite catch that. "
            "Could you please say it again?"
        )
        return listen()   # recursive retry
