"""
URLYZE AI - production entry point.
One service serves both the API (from main.py) and the built website (frontend/dist).

Run:  uvicorn prod:app --host 0.0.0.0 --port $PORT
"""
import os
import sqlite3
from pathlib import Path

from fastapi.staticfiles import StaticFiles

import auth
import db
from main import app  # all API routes are defined in main.py (it also creates the database tables)

# Optional demo account. Free hosting wipes local files on restart, so this account is
# re-created at every start-up when DEMO_EMAIL and DEMO_PASSWORD are set as environment variables.
_email = os.environ.get("DEMO_EMAIL", "").strip().lower()
_password = os.environ.get("DEMO_PASSWORD", "")
if _email and len(_password) >= 8 and not db.get_user_by_email(_email):
    try:
        db.create_user(_email, "Demo User", auth.hash_password(_password))
    except sqlite3.IntegrityError:
        pass

# Serve the website last, so the API routes above always win.
DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="site")
