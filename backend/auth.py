"""
Password hashing + signed login tokens, using only the Python standard library.

- Passwords: PBKDF2-HMAC-SHA256 with a random salt (never stored in plain text).
- Tokens: JWT-format (HS256) signed with a secret key kept in backend/data/secret.key.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
KEY_FILE = DATA_DIR / "secret.key"
ITERATIONS = 600_000


def _load_secret() -> bytes:
    if KEY_FILE.exists():
        return bytes.fromhex(KEY_FILE.read_text().strip())
    key = secrets.token_bytes(32)
    KEY_FILE.write_text(key.hex())
    return key


SECRET = _load_secret()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# used so a login for an unknown email takes the same time as a real one
DUMMY_HASH = hash_password("not-a-real-password")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(message: str) -> str:
    return _b64(hmac.new(SECRET, message.encode(), hashlib.sha256).digest())


def make_token(user_id: int, hours: int = 12) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": user_id, "exp": int(time.time()) + hours * 3600},
                              separators=(",", ":")).encode())
    return f"{header}.{payload}.{_sign(header + '.' + payload)}"


def read_token(token: str):
    """Returns the user id, or None if the token is invalid or expired."""
    try:
        header, payload, sig = token.split(".")
        if not hmac.compare_digest(sig, _sign(header + "." + payload)):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < time.time():
            return None
        return int(data["sub"])
    except Exception:
        return None


# --- simple brute-force protection: 5 failed logins per email per 5 minutes ---
_FAILS: dict = {}
WINDOW, MAX_FAILS = 300, 5


def too_many_attempts(email: str) -> bool:
    now = time.time()
    _FAILS[email] = [t for t in _FAILS.get(email, []) if now - t < WINDOW]
    return len(_FAILS[email]) >= MAX_FAILS


def record_fail(email: str):
    _FAILS.setdefault(email, []).append(time.time())


def clear_fails(email: str):
    _FAILS.pop(email, None)
