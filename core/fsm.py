"""
Finite State Machine Engine
═══════════════════════════
Lightweight, explicit FSM for the patrol robot.
Each state has optional on_enter/on_exit hooks.
"""

import time


class FSM:
    """
    States
    ------
    PATROL   – idle, ready to scan environment
    SCAN     – servo is sweeping, looking for humans
    ROAM     – driving forward with obstacle avoidance
    APPROACH – moving toward a detected human
    IDENTIFY – close enough, running face recognition
    INTERACT – conversation / greeting in progress
    WAIT_DECISION – waiting for Telegram response
    RESUME   – brief transition back to PATROL
    """

    PATROL        = "PATROL"
    SCAN          = "SCAN"
    ROAM          = "ROAM"
    APPROACH      = "APPROACH"
    IDENTIFY      = "IDENTIFY"
    INTERACT      = "INTERACT"
    WAIT_DECISION = "WAIT_DECISION"
    RESUME        = "RESUME"

    # Valid transitions: source → {allowed targets}
    _TRANSITIONS = {
        PATROL:        {SCAN},
        SCAN:          {ROAM, APPROACH, PATROL},
        ROAM:          {SCAN, APPROACH, PATROL},
        APPROACH:      {IDENTIFY, PATROL},
        IDENTIFY:      {INTERACT, PATROL},
        INTERACT:      {WAIT_DECISION, PATROL},
        WAIT_DECISION: {PATROL},
        RESUME:        {PATROL},
    }

    ALL_STATES = set(_TRANSITIONS.keys())

    def __init__(self):
        self._state = self.PATROL
        self._enter_time = time.time()
        self._on_enter = {}   # state → callable
        self._on_exit  = {}   # state → callable
        print(f"🤖 FSM initialised → {self._state}")

    # ── Properties ────────────────────────────────────────────
    @property
    def state(self) -> str:
        return self._state

    @property
    def time_in_state(self) -> float:
        """Seconds since we entered the current state."""
        return time.time() - self._enter_time

    # ── Hook Registration ─────────────────────────────────────
    def on_enter(self, state: str, callback):
        """Register a function to call when *entering* a state."""
        self._on_enter[state] = callback

    def on_exit(self, state: str, callback):
        """Register a function to call when *leaving* a state."""
        self._on_exit[state] = callback

    # ── Transition ────────────────────────────────────────────
    def transition(self, new_state: str) -> bool:
        """
        Attempt a state transition.
        Returns True if the transition was valid, False otherwise.
        """
        if new_state == self._state:
            return True                      # no-op, not an error

        allowed = self._TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            print(
                f"⚠️  FSM: invalid transition {self._state} → {new_state} "
                f"(allowed: {allowed})"
            )
            return False

        old = self._state

        # Exit hook
        if old in self._on_exit:
            self._on_exit[old]()

        self._state = new_state
        self._enter_time = time.time()

        # Enter hook
        if new_state in self._on_enter:
            self._on_enter[new_state]()

        print(f"🔄 FSM: {old} → {new_state}")
        return True

    def force(self, state: str):
        """
        Force-set state without validation.
        Use only for error recovery / reset.
        """
        old = self._state
        self._state = state
        self._enter_time = time.time()
        print(f"⚡ FSM: force {old} → {state}")

    def is_state(self, *states: str) -> bool:
        """Check if current state is any of the given states."""
        return self._state in states
