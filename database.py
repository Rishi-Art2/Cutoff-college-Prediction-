# """
# database.py
# -----------
# All SQL (SQLite) logic for the Cutoff College Predictor app lives here:
# - users table        -> login / signup data
# - predictions table   -> history of every search a logged-in user makes

# SQLite is used because it needs zero setup (no server, no extra services)
# and ships built into Python, which makes it perfect for a college project.
# The .db file (cutoff_predictor.db) is created automatically the first time
# the app runs.
# """

import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cutoff_predictor.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist. Safe to call every run."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            percentile REAL,
            category TEXT,
            branch TEXT,
            cap_round TEXT,
            results_count INTEGER,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()

    # --- Lightweight migration for anyone running this on an older DB file
    # that was created before the cap_round column existed ---
    cur.execute("PRAGMA table_info(predictions)")
    existing_cols = {row["name"] for row in cur.fetchall()}
    if "cap_round" not in existing_cols:
        cur.execute("ALTER TABLE predictions ADD COLUMN cap_round TEXT")
        conn.commit()

    conn.close()


def hash_password(password: str) -> str:
    """
    Simple SHA-256 hashing so plain-text passwords are never stored.
    NOTE: for a real production app use a salted algorithm like bcrypt
    or argon2 instead -- SHA-256 alone is fine for a college project demo.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def add_user(username: str, email: str, password: str):
    """Insert a new user. Returns (success: bool, message: str)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username.strip(), email.strip(), hash_password(password)),
        )
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "That username or email is already registered."
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    """Returns the user row (as dict) if credentials match, else None.
    Accepts either the registered username or email in the `username` field.
    """
    conn = get_connection()
    cur = conn.cursor()
    identifier = username.strip().lower()
    cur.execute(
        "SELECT * FROM users WHERE (LOWER(username) = ? OR LOWER(email) = ?) AND password = ?",
        (identifier, identifier, hash_password(password)),
    )
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

def save_prediction(
    user_id: int,
    percentile: float,
    category: str,
    branch: str,
    cap_round: str,
    results_count: int,
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO predictions (user_id, percentile, category, branch, cap_round, results_count)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, percentile, category, branch, cap_round, results_count),
    )
    conn.commit()
    conn.close()


def get_user_predictions(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM predictions WHERE user_id = ? ORDER BY searched_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_users():
    """Used by the Admin Dashboard page to show everyone stored in SQL."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_predictions():
    """Used by the Admin Dashboard page to show every search across all users."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT predictions.id, users.username, percentile, category, branch,
                  cap_round, results_count, searched_at
           FROM predictions
           JOIN users ON users.id = predictions.user_id
           ORDER BY searched_at DESC"""
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]