"""Password hashing, JWT creation/decoding, email OTP utilities."""

from __future__ import annotations

import hashlib
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Optional

# ── Password strength ──────────────────────────────────────────────────────────

PASSWORD_RULES_MSG = (
    "Password must be at least 8 characters and include uppercase, lowercase, "
    "number, and special character. Only English letters, numbers, and symbols are allowed."
)

_SPECIAL = re.compile(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/`~\\]')
_NON_ASCII_OR_SPACE = re.compile(r'[^\x21-\x7E]')  # rejects space + non-ASCII


def validate_password_strength(password: str) -> str:
    """Raises ValueError if password does not meet strength requirements."""
    if len(password) < 8:
        raise ValueError(PASSWORD_RULES_MSG)
    if _NON_ASCII_OR_SPACE.search(password):
        raise ValueError(PASSWORD_RULES_MSG)
    if not any(c.isupper() and c.isascii() for c in password):
        raise ValueError(PASSWORD_RULES_MSG)
    if not any(c.islower() and c.isascii() for c in password):
        raise ValueError(PASSWORD_RULES_MSG)
    if not any(c.isdigit() for c in password):
        raise ValueError(PASSWORD_RULES_MSG)
    if not _SPECIAL.search(password):
        raise ValueError(PASSWORD_RULES_MSG)
    return password

from jose import jwt
from passlib.context import CryptContext

from backend.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    EMAIL_FROM,
    SECRET_KEY,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
    TEMP_TOKEN_EXPIRE_MINUTES,
)

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(subject: str | int, extra: Optional[dict] = None) -> str:
    now = datetime.now(timezone.utc)
    data: dict = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra:
        data.update(extra)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def create_temp_token(subject: str | int) -> str:
    """Short-lived token issued mid-login when 2FA is required."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(subject),
            "iat": now,
            "exp": now + timedelta(minutes=TEMP_TOKEN_EXPIRE_MINUTES),
            "scope": "2fa",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Returns payload dict. Raises jose.JWTError on invalid/expired tokens."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── Email OTP ─────────────────────────────────────────────────────────────────

def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def verify_otp_hash(code: str, stored_hash: str) -> bool:
    import hmac as _hmac
    computed = hashlib.sha256(code.encode()).hexdigest()
    return _hmac.compare_digest(computed, stored_hash)


def generate_reset_token() -> str:
    """Returns a URL-safe 32-byte random token (not stored — only its hash is)."""
    return secrets.token_urlsafe(32)


# ── Token revocation blacklist ─────────────────────────────────────────────────

import threading as _threading

_revoked_tokens: dict[str, "datetime"] = {}
_revoked_lock = _threading.Lock()


def revoke_token(token: str) -> None:
    """Add a JWT to the blacklist until its natural expiry."""
    try:
        from jose import jwt as _jwt
        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    except Exception:
        return
    with _revoked_lock:
        _revoked_tokens[token] = exp
        now = datetime.now(timezone.utc)
        expired = [t for t, e in _revoked_tokens.items() if e < now]
        for t in expired:
            del _revoked_tokens[t]


def is_token_revoked(token: str) -> bool:
    with _revoked_lock:
        return token in _revoked_tokens


def send_reset_code_email(to_email: str, code: str) -> None:
    """Send a 6-digit verification code for password reset (NOT a login code)."""
    body = (
        f"You requested a password reset for your NucleiAI account.\n\n"
        f"Your verification code is:\n\n"
        f"    {code}\n\n"
        f"This code expires in 10 minutes.\n\n"
        f"Enter this code on the reset page — it will NOT log you in.\n\n"
        f"If you did not request this, you can safely ignore this email."
    )
    msg = MIMEText(body)
    msg["Subject"] = "NucleiAI — Password reset code"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[DEV RESET CODE] → {to_email}  code: {code}")
        return

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def send_otp_email(to_email: str, code: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        # Dev fallback: print to console so flow works without SMTP config
        print(f"[DEV EMAIL OTP] → {to_email}  code: {code}")
        return

    msg = MIMEText(
        f"Your NucleiAI verification code is:\n\n    {code}\n\nValid for 10 minutes."
    )
    msg["Subject"] = "NucleiAI Verification Code"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)
