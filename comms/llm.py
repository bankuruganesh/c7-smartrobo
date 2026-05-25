"""
LLM — Ollama Helpers
════════════════════
Natural language processing for visitor conversations.
Extracted from robot_merged.py lines 411–539.
"""

import ollama
from difflib import get_close_matches
import config


# ── Core Ollama Call ──────────────────────────────────────────

def ollama_chat(system: str, user: str) -> str:
    """Single-turn Ollama chat.  Returns stripped response or empty string."""
    try:
        response = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        return response["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️  Ollama error: {e}")
        return ""


# ── Employee Name Fuzzy Match ─────────────────────────────────

def match_person(raw: str) -> str | None:
    """Fuzzy-match a raw string to known employee names."""
    result = get_close_matches(
        raw.lower().strip(),
        config.USER_CHAT_IDS.keys(),
        n=1, cutoff=0.6,
    )
    return result[0] if result else None


# ── Extraction Helpers ────────────────────────────────────────

_KNOWN_EMPLOYEES = ", ".join(config.KNOWN_EMPLOYEES)


def extract_name(utterance: str) -> str | None:
    """Extract a visitor's name from an utterance."""
    reply = ollama_chat(
        system=(
            "You extract a person's name from a sentence. "
            "Reply with ONLY the name (capitalised). "
            "If no name is present reply with exactly: NONE"
        ),
        user=utterance,
    )
    reply = reply.strip().strip(".,!?\"'")
    if reply.upper() == "NONE" or not reply:
        return None
    if len(reply.split()) > 4:
        return None
    return reply.capitalize()


def extract_person(utterance: str) -> str | None:
    """Extract the employee a visitor wants to meet."""
    reply = ollama_chat(
        system=(
            f"You extract the name of an employee a visitor wants to meet. "
            f"Known employees: {_KNOWN_EMPLOYEES}. "
            f"Reply with ONLY the employee name (lowercase). "
            f"If none found reply with exactly: NONE"
        ),
        user=utterance,
    )
    reply = reply.strip().strip(".,!?\"'").lower()
    if reply == "none" or not reply:
        return None
    return match_person(reply)


def extract_purpose(utterance: str) -> str | None:
    """Extract the purpose of a visit from an utterance."""
    reply = ollama_chat(
        system=(
            "You extract the purpose or reason for a visit from a sentence. "
            "Reply with a short phrase (max 10 words). "
            "If no purpose is mentioned reply with exactly: NONE"
        ),
        user=utterance,
    )
    reply = reply.strip().strip(".,!?\"'")
    if reply.upper() == "NONE" or not reply:
        return None
    return reply


# ── Response Generators ──────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are ARIA, a friendly professional front-desk receptionist robot. "
    "Keep replies to 1–2 short sentences."
)


def gen_greeting(known_name: str | None) -> str:
    if known_name:
        prompt = (
            f"Greet the returning visitor named {known_name} warmly (1 sentence) "
            "and ask who they are here to meet today."
        )
    else:
        prompt = "Greet a new visitor warmly (1 sentence) and ask for their name."
    return ollama_chat(system=_SYSTEM_PROMPT, user=prompt)


def gen_ask_person(visitor_name: str) -> str:
    return ollama_chat(
        system=_SYSTEM_PROMPT,
        user=f"The visitor's name is {visitor_name}. Ask them naturally who they would like to meet.",
    )


def gen_person_not_found(raw: str) -> str:
    return ollama_chat(
        system=_SYSTEM_PROMPT,
        user=(
            f"The visitor said they want to meet '{raw}' but that person is not in the system. "
            f"Politely tell them and ask if they mean one of: {_KNOWN_EMPLOYEES}."
        ),
    )


def gen_ask_purpose(visitor_name: str, person: str) -> str:
    return ollama_chat(
        system=_SYSTEM_PROMPT,
        user=f"Visitor {visitor_name} wants to meet {person}. Ask them naturally what their purpose of visit is.",
    )


def gen_confirm(visitor_name: str, person: str, purpose: str) -> str:
    return ollama_chat(
        system=_SYSTEM_PROMPT,
        user=(
            f"Confirm these details with the visitor in a natural, friendly way: "
            f"Name={visitor_name}, Meeting={person}, Purpose={purpose}. "
            f"Ask if everything is correct."
        ),
    )


def gen_clarify(field: str) -> str:
    prompts = {
        "name":    "Politely ask the visitor for their name again, as you didn't catch it.",
        "person":  f"Politely ask the visitor again who they would like to meet. Known employees: {_KNOWN_EMPLOYEES}.",
        "purpose": "Politely ask the visitor again what the purpose of their visit is.",
    }
    return ollama_chat(
        system=_SYSTEM_PROMPT,
        user=prompts.get(field, "Politely ask the visitor to repeat themselves."),
    )
