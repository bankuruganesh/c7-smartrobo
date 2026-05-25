"""
SQLite Visitor Log Database
═══════════════════════════
Extracted from robot_merged.py lines 184–213.
Uses context manager for safe connection handling.
"""

import sqlite3
import config


def init_db():
    """Create the visitors table if it doesn't exist."""
    with sqlite3.connect(config.SQLITE_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    DEFAULT (datetime('now','localtime')),
                name       TEXT,
                purpose    TEXT,
                person     TEXT,
                decision   TEXT,
                image_path TEXT
            )
        """)
        conn.commit()
    print("✅ SQLite visitor log ready.")


def save_log(name: str, purpose: str, person: str,
             decision: str, image_path: str):
    """Insert a visitor record into the database."""
    try:
        with sqlite3.connect(config.SQLITE_DB_PATH) as conn:
            conn.execute(
                "INSERT INTO visitors (name, purpose, person, decision, image_path) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, purpose, person, decision, image_path),
            )
            conn.commit()
        print("✅ Visitor log saved to visitors.db.")
    except Exception as e:
        print(f"❌ DB Error: {e}")


# Initialise on import
init_db()
