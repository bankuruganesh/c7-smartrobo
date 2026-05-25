"""
Visitor Conversation — Multi-Turn Dialogue
═══════════════════════════════════════════
Full conversation pipeline: name → who to meet → purpose → confirm.
Extracted from robot_merged.py lines 542–623.
"""

from comms.tts import speak
from comms.stt import listen, reset_fail_counter, ConversationAborted
from comms import llm


def visitor_conversation(known_name: str = None) -> dict:
    """
    Conduct full multi-turn visitor conversation.

    Parameters
    ----------
    known_name : str or None — if returning visitor, pre-fill name

    Returns
    -------
    dict with keys: "name", "person", "purpose"

    Raises
    ------
    ConversationAborted — if STT fails too many times
    """
    reset_fail_counter()

    confirmed_name    = known_name.strip().capitalize() if known_name else None
    confirmed_person  = None
    confirmed_purpose = None
    max_retries       = 3

    # ── STEP 1 — NAME ────────────────────────────────────────
    speak(llm.gen_greeting(known_name))

    if not confirmed_name:
        for _ in range(max_retries):
            user_text      = listen()
            confirmed_name = llm.extract_name(user_text)
            if confirmed_name:
                print(f"  ✔ Name confirmed: {confirmed_name}")
                break
            speak(llm.gen_clarify("name"))
        if not confirmed_name:
            confirmed_name = "Visitor"

    # ── STEP 2 — WHO TO MEET ─────────────────────────────────
    speak(llm.gen_ask_person(confirmed_name))

    for _ in range(max_retries):
        user_text        = listen()
        confirmed_person = llm.extract_person(user_text)

        if confirmed_person:
            print(f"  ✔ Person confirmed: {confirmed_person}")
            # Bonus: try to extract purpose from same utterance
            if confirmed_purpose is None:
                bonus = llm.extract_purpose(user_text)
                if bonus:
                    confirmed_purpose = bonus
                    print(f"  ✔ Purpose (bonus): {confirmed_purpose}")
            break

        raw_guess = (
            user_text.strip().split()[-1]
            if user_text.strip() else "that person"
        )
        speak(llm.gen_person_not_found(raw_guess))

    if not confirmed_person:
        confirmed_person = "unknown"

    # ── STEP 3 — PURPOSE ─────────────────────────────────────
    if not confirmed_purpose:
        speak(llm.gen_ask_purpose(confirmed_name, confirmed_person))

        for _ in range(max_retries):
            user_text         = listen()
            confirmed_purpose = llm.extract_purpose(user_text)
            if confirmed_purpose:
                print(f"  ✔ Purpose confirmed: {confirmed_purpose}")
                break
            speak(llm.gen_clarify("purpose"))

        if not confirmed_purpose:
            confirmed_purpose = "not specified"

    # ── STEP 4 — CONFIRM ─────────────────────────────────────
    speak(llm.gen_confirm(confirmed_name, confirmed_person, confirmed_purpose))
    user_text = listen()

    negative_words = {"no", "nope", "wrong", "incorrect", "not", "nah"}
    if any(w in user_text.lower().split() for w in negative_words):
        speak("I'm sorry about that! Let me start over.")
        return visitor_conversation(known_name=known_name)

    result = {
        "name":    confirmed_name,
        "person":  confirmed_person,
        "purpose": confirmed_purpose,
    }
    print(f"  ✅ Visitor info confirmed → {result}")
    return result
