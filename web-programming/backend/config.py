"""Central configuration — all values read from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nuclei.db")

_raw_secret = os.getenv("SECRET_KEY", "")
if not _raw_secret:
    if os.getenv("ENV", "development") == "production":
        raise ValueError("SECRET_KEY env var is required in production")
    _raw_secret = "dev-secret-change-in-production"

SECRET_KEY: str = _raw_secret
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
TEMP_TOKEN_EXPIRE_MINUTES: int = 5

FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
ENV: str = os.getenv("ENV", "development")

# OAuth providers (empty string = provider disabled)
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
DROPBOX_CLIENT_ID: str = os.getenv("DROPBOX_CLIENT_ID", "")
DROPBOX_CLIENT_SECRET: str = os.getenv("DROPBOX_CLIENT_SECRET", "")

# Email (SMTP) — for Email OTP
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM: str = os.getenv("EMAIL_FROM", os.getenv("SMTP_USER", "noreply@nuclei.app"))
