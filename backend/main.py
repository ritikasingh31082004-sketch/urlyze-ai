"""
URLYZE AI - FastAPI backend.
Run:  uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import analyzer
import auth
import db
import email_analyzer

db.init_db()

app = FastAPI(title="URLYZE AI", version="2.0",
              description="Phishing URL and email detection with user accounts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = Path(__file__).resolve().parents[1] / "ml" / "reports"
if REPORTS_DIR.exists():
    app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


class RegisterRequest(BaseModel):
    name: str = ""
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ScanRequest(BaseModel):
    url: str


class EmailRequest(BaseModel):
    text: str


def public_user(u: dict) -> dict:
    return {"id": u["id"], "name": u["name"], "email": u["email"]}


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please log in.")
    user_id = auth.read_token(authorization[7:].strip())
    user = db.get_user_by_id(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    return user


# ---------------- public ----------------
@app.get("/health")
def health():
    return {"status": "ok", "model": analyzer.MODEL_NAME}


@app.get("/model-info")
def model_info():
    return analyzer.model_info()


# ---------------- accounts ----------------
@app.post("/auth/register")
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    name = req.name.strip()[:60]
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if len(req.password) > 128:
        raise HTTPException(status_code=400, detail="Password is too long (max 128 characters).")
    try:
        user_id = db.create_user(email, name, auth.hash_password(req.password))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    return {"token": auth.make_token(user_id), "user": public_user(db.get_user_by_id(user_id))}


@app.post("/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    if auth.too_many_attempts(email):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Please wait a few minutes and try again.")
    user = db.get_user_by_email(email)
    ok = auth.verify_password(req.password, user["password_hash"] if user else auth.DUMMY_HASH)
    if not user or not ok:
        auth.record_fail(email)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    auth.clear_fails(email)
    return {"token": auth.make_token(user["id"]), "user": public_user(user)}


@app.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return public_user(user)


# ---------------- scanning (login required) ----------------
@app.post("/predict")
def predict(req: ScanRequest, user: dict = Depends(current_user)):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please enter a URL.")
    if len(url) > 2048:
        raise HTTPException(status_code=400, detail="URL is too long (max 2048 characters).")
    if " " in url:
        raise HTTPException(status_code=400, detail="A URL cannot contain spaces.")
    result = analyzer.analyze(url)
    result["scanned_at"] = datetime.now(timezone.utc).isoformat()
    db.add_scan(user["id"], "url", result["url"][:300], result["risk_score"], result["level"], result["verdict"])
    return result


@app.post("/email-check")
def email_check(req: EmailRequest, user: dict = Depends(current_user)):
    text = req.text.strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Please paste the email text (at least a few words).")
    if len(text) > 20000:
        raise HTTPException(status_code=400, detail="Email is too long (max 20,000 characters).")
    result = email_analyzer.analyze_email(text)
    result["scanned_at"] = datetime.now(timezone.utc).isoformat()
    subject = result["subject"] or " ".join(text.split())[:80]
    db.add_scan(user["id"], "email", subject[:200], result["risk_score"], result["level"], result["verdict"])
    return result


@app.get("/history")
def history(user: dict = Depends(current_user)):
    return db.list_scans(user["id"])


@app.delete("/history")
def clear_history(user: dict = Depends(current_user)):
    db.clear_scans(user["id"])
    return {"ok": True}
