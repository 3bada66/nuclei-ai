"""Tests for the 3-step forgot-password / verify-code / reset-password flow."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.auth_utils import generate_otp, generate_reset_token, hash_otp
from backend.main import _RESET_CODE_PREFIX
from backend.tests.conftest import register_and_login


# ── Helpers ───────────────────────────────────────────────────────────────────

def _plant_reset_token(session, email: str) -> str:
    """Bypass the code step: plant a ready-to-use reset token directly in the DB."""
    from backend.models import User
    from sqlmodel import select
    token = generate_reset_token()
    user = session.exec(select(User).where(User.email == email)).first()
    user.reset_token_hash = hash_otp(token)
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    session.add(user)
    session.commit()
    return token


def _plant_reset_code(session, email: str) -> str:
    """Plant a 6-digit reset code in the DB and return the raw code."""
    from backend.models import User
    from sqlmodel import select
    code = generate_otp()
    user = session.exec(select(User).where(User.email == email)).first()
    user.reset_token_hash = _RESET_CODE_PREFIX + hash_otp(code)
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    session.add(user)
    session.commit()
    return code


# ── 1. Existing email sends code ──────────────────────────────────────────────

def test_forgot_password_existing_email(client: TestClient):
    register_and_login(client, "reset1", "reset1@test.com")
    r = client.post("/auth/forgot-password", json={"email": "reset1@test.com"})
    assert r.status_code == 200
    assert "code" in r.json()["message"].lower()


# ── 2. Non-existing email — same response (anti-enumeration) ──────────────────

def test_forgot_password_nonexistent_email(client: TestClient):
    r = client.post("/auth/forgot-password", json={"email": "nobody@nowhere.com"})
    assert r.status_code == 200
    assert "code" in r.json()["message"].lower()


# ── 3. Valid code → reset_token returned (NOT a login token) ─────────────────

def test_verify_reset_code_returns_reset_token_not_login(client: TestClient, session):
    register_and_login(client, "reset3", "reset3@test.com")
    code = _plant_reset_code(session, "reset3@test.com")

    r = client.post("/auth/verify-reset-code", json={"email": "reset3@test.com", "code": code})
    assert r.status_code == 200
    data = r.json()
    assert "reset_token" in data
    assert "access_token" not in data       # must NOT be a login token
    assert "token_type" not in data         # must NOT look like a JWT response
    assert data["message"] == "Code verified. You can now reset your password."


# ── 4. Valid reset_token resets password ──────────────────────────────────────

def test_reset_password_valid_token(client: TestClient, session):
    register_and_login(client, "reset4", "reset4@test.com")
    token = _plant_reset_token(session, "reset4@test.com")

    r = client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass99!"})
    assert r.status_code == 200
    assert "successfully" in r.json()["message"].lower()


# ── 5. Raw 6-digit code cannot be used directly on /reset-password ────────────

def test_raw_code_rejected_by_reset_password(client: TestClient, session):
    register_and_login(client, "reset5", "reset5@test.com")
    code = _plant_reset_code(session, "reset5@test.com")
    # Attempt to use the raw code on the reset endpoint — must fail
    r = client.post("/auth/reset-password", json={"token": code, "new_password": "NewPass99!"})
    assert r.status_code == 400


# ── 6. Expired code rejected ──────────────────────────────────────────────────

def test_verify_reset_code_expired(client: TestClient, session):
    from backend.models import User
    from sqlmodel import select
    register_and_login(client, "reset6", "reset6@test.com")
    code = generate_otp()
    user = session.exec(select(User).where(User.email == "reset6@test.com")).first()
    user.reset_token_hash = _RESET_CODE_PREFIX + hash_otp(code)
    user.reset_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.add(user); session.commit()

    r = client.post("/auth/verify-reset-code", json={"email": "reset6@test.com", "code": code})
    assert r.status_code == 400


# ── 7. Invalid code rejected ──────────────────────────────────────────────────

def test_verify_reset_code_wrong_code(client: TestClient, session):
    register_and_login(client, "reset7", "reset7@test.com")
    _plant_reset_code(session, "reset7@test.com")

    r = client.post("/auth/verify-reset-code", json={"email": "reset7@test.com", "code": "000000"})
    assert r.status_code == 400


# ── 8. Expired reset_token rejected ──────────────────────────────────────────

def test_reset_password_expired_token(client: TestClient, session):
    from backend.models import User
    from sqlmodel import select
    register_and_login(client, "reset8", "reset8@test.com")
    token = generate_reset_token()
    user = session.exec(select(User).where(User.email == "reset8@test.com")).first()
    user.reset_token_hash = hash_otp(token)
    user.reset_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.add(user); session.commit()

    r = client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass99!"})
    assert r.status_code == 400


# ── 9. Invalid reset_token rejected ──────────────────────────────────────────

def test_reset_password_invalid_token(client: TestClient):
    r = client.post("/auth/reset-password", json={"token": "totallywrongtoken", "new_password": "NewPass99!"})
    assert r.status_code == 400


# ── 10. Token is single-use ───────────────────────────────────────────────────

def test_reset_password_token_single_use(client: TestClient, session):
    register_and_login(client, "reset10", "reset10@test.com")
    token = _plant_reset_token(session, "reset10@test.com")

    client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass99!"})
    r = client.post("/auth/reset-password", json={"token": token, "new_password": "AnotherP1!"})
    assert r.status_code == 400


# ── 11. Weak password rejected ────────────────────────────────────────────────

def test_reset_password_weak_password_rejected(client: TestClient, session):
    register_and_login(client, "reset11", "reset11@test.com")
    token = _plant_reset_token(session, "reset11@test.com")

    r = client.post("/auth/reset-password", json={"token": token, "new_password": "onlyletters"})
    assert r.status_code == 422


# ── 12. Login with new password succeeds ─────────────────────────────────────

def test_login_with_new_password(client: TestClient, session):
    register_and_login(client, "reset12", "reset12@test.com", "OldPass1!")
    token = _plant_reset_token(session, "reset12@test.com")
    client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass99!"})

    r = client.post("/auth/login", json={"email": "reset12@test.com", "password": "NewPass99!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


# ── 13. Old password rejected after reset ────────────────────────────────────

def test_old_password_rejected_after_reset(client: TestClient, session):
    register_and_login(client, "reset13", "reset13@test.com", "OldPass1!")
    token = _plant_reset_token(session, "reset13@test.com")
    client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass99!"})

    r = client.post("/auth/login", json={"email": "reset13@test.com", "password": "OldPass1!"})
    assert r.status_code == 401


# ── 14. Full 3-step flow end-to-end ──────────────────────────────────────────

def test_full_reset_flow(client: TestClient, session):
    register_and_login(client, "reset14", "reset14@test.com", "OldPass1!")

    # Step 1: request code
    r1 = client.post("/auth/forgot-password", json={"email": "reset14@test.com"})
    assert r1.status_code == 200

    # Step 2: verify code (plant it since we can't read email in tests)
    code = _plant_reset_code(session, "reset14@test.com")
    r2 = client.post("/auth/verify-reset-code", json={"email": "reset14@test.com", "code": code})
    assert r2.status_code == 200
    reset_token = r2.json()["reset_token"]
    assert "access_token" not in r2.json()

    # Step 3: set new password
    r3 = client.post("/auth/reset-password", json={"token": reset_token, "new_password": "NewPass99!"})
    assert r3.status_code == 200

    # Old password no longer works
    assert client.post("/auth/login", json={"email": "reset14@test.com", "password": "OldPass1!"}).status_code == 401
    # New password works
    assert client.post("/auth/login", json={"email": "reset14@test.com", "password": "NewPass99!"}).status_code == 200
