# """
# database.py
# -----------
# All SQL logic for the Cutoff College Predictor app, backed by a hosted
# PostgreSQL database (e.g. Supabase or Neon) so data survives app restarts --
# unlike a local SQLite file, which resets every time a Streamlit Community
# Cloud app sleeps/restarts.

# Connection details are read from Streamlit secrets:
# - Locally: .streamlit/secrets.toml (NEVER commit this file to GitHub)
# - On Streamlit Community Cloud: your app's Settings -> Secrets

# Expected secrets.toml shape:

#     [postgres]
#     host = "db.xxxxxxxxxxxx.supabase.co"
#     port = 5432
#     dbname = "postgres"
#     user = "postgres"
#     password = "your-db-password"
#     sslmode = "require"

# See README.md for how to get these values from Supabase.
# """

import hashlib

import psycopg2
import psycopg2.errors
import psycopg2.extras
import streamlit as st


def get_connection():
    creds = st.secrets["postgres"]
    conn = psycopg2.connect(
        host=creds["host"],
        port=creds.get("port", 5432),
        dbname=creds["dbname"],
        user=creds["user"],
        password=creds["password"],
        sslmode=creds.get("sslmode", "require"),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    return conn


def init_db():
    """Create tables if they don't already exist. Safe to call every run."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users (id),
            percentile REAL,
            category TEXT,
            branch TEXT,
            cap_round TEXT,
            results_count INTEGER,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Safe no-op if the column already exists -- handles upgrades cleanly.
    cur.execute("ALTER TABLE predictions ADD COLUMN IF NOT EXISTS cap_round TEXT")
    conn.commit()
    cur.close()
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
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username.strip(), email.strip(), hash_password(password)),
        )
        conn.commit()
        return True, "Account created successfully!"
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "That username or email is already registered."
    finally:
        cur.close()
        conn.close()


def authenticate_user(username: str, password: str):
    """Returns the user row (as dict) if credentials match, else None.
    Username match is case-insensitive; password matching stays case-sensitive.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(%s) AND password = %s",
        (username.strip(), hash_password(password)),
    )
    user = cur.fetchone()
    cur.close()
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
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, percentile, category, branch, cap_round, results_count),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_user_predictions(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM predictions WHERE user_id = %s ORDER BY searched_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_all_users():
    """Used by the Admin Dashboard page to show everyone stored in SQL."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
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
    cur.close()
    conn.close()
    return [dict(r) for r in rows]
