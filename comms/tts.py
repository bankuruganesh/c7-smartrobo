"""
Text-to-Speech — Piper TTS
═══════════════════════════
Offline TTS via Piper subprocess + pygame playback.
Extracted from robot_merged.py lines 218–275.
"""

import subprocess
import os
import time
import pygame
import config

# Initialise pygame mixer ONCE at import
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.mixer.init()


def speak(text: str, state_label: str = ""):
    """
    Synthesise and play speech.  Blocking until playback finishes.

    Parameters
    ----------
    text : str          — text to speak
    state_label : str   — optional FSM state for log prefix
    """
    prefix = f"  [{state_label}] " if state_label else "  "
    print(f"{prefix}Robot: {text}")

    try:
        if os.path.exists(config.PIPER_OUTPUT):
            os.remove(config.PIPER_OUTPUT)

        result = subprocess.run(
            [
                "piper",
                "--model",        config.PIPER_MODEL,
                "--output_file",  config.PIPER_OUTPUT,
                "--length_scale", config.PIPER_LENGTH_SCALE,
            ],
            input=text,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"  Piper error: {result.stderr}")
            return

        # Wait for file flush
        for _ in range(20):
            if (os.path.exists(config.PIPER_OUTPUT) and
                    os.path.getsize(config.PIPER_OUTPUT) > 0):
                break
            time.sleep(0.05)
        else:
            print("  Piper: output file never appeared.")
            return

        pygame.mixer.music.load(config.PIPER_OUTPUT)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.unload()
        os.remove(config.PIPER_OUTPUT)

    except subprocess.TimeoutExpired:
        print("  Piper TTS timed out.")
    except Exception as e:
        print(f"  Piper TTS Error: {e}")


def cleanup():
    """Shutdown pygame mixer."""
    pygame.mixer.quit()
