"""SQLite storage for users and scan history (single file: backend/data/urlyze.db)."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "urlyze.db"


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _db() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                subject TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                level TEXT NOT NULL,
                verdict TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_scans_user ON scans(user_id, id DESC);
            """
        )


def _now():
    return datetime.now(timezone.utc).isoformat()


def create_user(email, name, password_hash):
    """Returns the new user id. Raises sqlite3.IntegrityError if the email exists."""
    with _db() as c:
        cur = c.execute(
            "INSERT INTO users (email, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (email, name, password_hash, _now()),
        )
        return cur.lastrowid


def get_user_by_email(email):
    with _db() as c:
        row = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with _db() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def add_scan(user_id, kind, subject, risk_score, level, verdict):
    with _db() as c:
        c.execute(
            "INSERT INTO scans (user_id, kind, subject, risk_score, level, verdict, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, kind, subject, risk_score, level, verdict, _now()),
        )


def list_scans(user_id, limit=50):
    with _db() as c:
        rows = c.execute(
            "SELECT id, kind, subject, risk_score, level, verdict, created_at "
            "FROM scans WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def clear_scans(user_id):
    with _db() as c:
        c.execute("DELETE FROM scans WHERE user_id = ?", (user_id,))
