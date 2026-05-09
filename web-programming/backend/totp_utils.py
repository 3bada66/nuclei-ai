"""TOTP (Time-based One-Time Password) helpers using pyotp."""

from __future__ import annotations

import pyotp


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = "NucleiAI") -> str:
    return pyotp.TOTP(secret).provisioning_uri(email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
