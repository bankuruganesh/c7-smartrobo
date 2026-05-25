"""
Face Database Manager
═════════════════════
Manages permanent (read-only) and visitor (read-write) pickle databases.
Singleton to avoid multiple loads.
Extracted from robot_merged.py lines 86–121.
"""

import pickle
import os
import config


class FaceDB:
    """Singleton face database manager."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._loaded = True

        # ── Permanent faces (read-only at runtime) ────────────
        try:
            with open(config.FACES_DB_PATH, "rb") as f:
                self._perm_enc, self._perm_names = pickle.load(f)
            print(f"✅ Permanent faces loaded: {self._perm_names}")
        except FileNotFoundError:
            self._perm_enc, self._perm_names = [], []
            print("⚠️  faces_db.pkl not found.")

        self._permanent_set = set(self._perm_names)

        # ── Visitor faces (read-write) ────────────────────────
        try:
            with open(config.VISITORS_DB_PATH, "rb") as f:
                self._vis_enc, self._vis_names = pickle.load(f)
            print(f"✅ Returning visitors loaded: {self._vis_names}")
        except FileNotFoundError:
            self._vis_enc, self._vis_names = [], []
            print("ℹ️  visitors_db.pkl not found — starting fresh.")

    # ── Properties ────────────────────────────────────────────
    @property
    def permanent_encodings(self):
        return self._perm_enc

    @property
    def permanent_names(self):
        return self._perm_names

    @property
    def permanent_name_set(self):
        return self._permanent_set

    @property
    def visitor_encodings(self):
        return self._vis_enc

    @property
    def visitor_names(self):
        return self._vis_names

    # ── Visitor Registration ──────────────────────────────────
    def register_visitor(self, encoding, name: str):
        """Append a first-time visitor's face encoding and save."""
        self._vis_enc.append(encoding)
        self._vis_names.append(name)
        self._save_visitors()
        print(f"✅ '{name}' registered in visitors_db.")

    def _save_visitors(self):
        """Persist visitor encodings to disk."""
        with open(config.VISITORS_DB_PATH, "wb") as f:
            pickle.dump((self._vis_enc, self._vis_names), f)
        print(f"💾 visitors_db.pkl updated ({len(self._vis_names)} visitors).")
