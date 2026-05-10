"""FastAPI dependency functions for auth and role enforcement."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session, select

from backend.auth_utils import decode_token
from backend.database import get_session
from backend.models import RevokedToken, User, UserRole

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token_hash = hashlib.sha256(creds.credentials.encode()).hexdigest()
    revoked = session.exec(
        select(RevokedToken).where(RevokedToken.token_hash == token_hash)
    ).first()
    if revoked:
        raise HTTPException(status_code=401, detail="Token has been revoked.")
    try:
        payload = decode_token(creds.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if payload.get("scope") == "2fa":
        raise HTTPException(status_code=401, detail="2FA not completed.")
    user = session.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


def get_temp_token_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    """Extract user_id from a 2FA temp token. Used only by /auth/2fa/verify."""
    if not creds:
        raise HTTPException(status_code=401, detail="Temp token required.")
    try:
        payload = decode_token(creds.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if payload.get("scope") != "2fa":
        raise HTTPException(status_code=401, detail="Not a 2FA intermediate token.")
    return int(payload["sub"])


def require_role(*roles: UserRole):
    """Factory that returns a dependency enforcing role membership."""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current_user
    return checker
