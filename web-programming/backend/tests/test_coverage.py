"""Tests targeting specific uncovered lines to achieve high coverage."""

import io
import struct
import zlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.auth_utils import (
    create_access_token,
    generate_otp,
    hash_otp,
    hash_password,
    send_otp_email,
    send_reset_code_email,
    validate_password_strength,
    verify_otp_hash,
)
from backend.crud import UserService
from backend.models import User, UserRole
from backend.tests.conftest import auth, register_and_login, register_and_login_as_admin


# ── validate_password_strength uncovered branches ─────────────────────────────

def test_password_too_short_raises():
    with pytest.raises(ValueError):
        validate_password_strength("Ab1!")


def test_password_no_lowercase_raises():
    with pytest.raises(ValueError):
        validate_password_strength("ABCDEFG1!")


def test_password_no_digit_raises():
    with pytest.raises(ValueError):
        validate_password_strength("Abcdefgh!")


def test_password_no_special_raises():
    with pytest.raises(ValueError):
        validate_password_strength("Abcdefg1")


def test_password_non_ascii_raises():
    with pytest.raises(ValueError):
        validate_password_strength("Abcd1!كلمة")


def test_password_space_raises():
    with pytest.raises(ValueError):
        validate_password_strength("Abcde 1!")


def test_password_valid_passes():
    assert validate_password_strength("TestPass1!") == "TestPass1!"


# ── create_access_token with extra data (line 78) ─────────────────────────────

def test_create_access_token_with_extra():
    token = create_access_token(42, extra={"scope": "2fa", "custom": "value"})
    from backend.auth_utils import decode_token
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["scope"] == "2fa"
    assert payload["custom"] == "value"


# ── verify_otp_hash returns False (line 113) ──────────────────────────────────

def test_verify_otp_hash_wrong_code():
    code = generate_otp()
    stored = hash_otp(code)
    assert verify_otp_hash("000000", stored) is False


def test_verify_otp_hash_correct_code():
    code = generate_otp()
    stored = hash_otp(code)
    assert verify_otp_hash(code, stored) is True


# ── SMTP email sending (mock smtplib) ─────────────────────────────────────────

def test_send_otp_email_uses_smtp_when_configured():
    mock_smtp = MagicMock()
    with patch("backend.auth_utils.SMTP_USER", "user@test.com"), \
         patch("backend.auth_utils.SMTP_PASSWORD", "secret"), \
         patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        send_otp_email("target@test.com", "123456")
        mock_smtp_class.assert_called_once()


def test_send_reset_code_email_uses_smtp_when_configured():
    mock_smtp = MagicMock()
    with patch("backend.auth_utils.SMTP_USER", "user@test.com"), \
         patch("backend.auth_utils.SMTP_PASSWORD", "secret"), \
         patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        send_reset_code_email("target@test.com", "654321")
        mock_smtp_class.assert_called_once()


def test_send_otp_email_prints_when_no_smtp(capsys):
    with patch("backend.auth_utils.SMTP_USER", ""), \
         patch("backend.auth_utils.SMTP_PASSWORD", ""):
        send_otp_email("target@test.com", "123456")
    captured = capsys.readouterr()
    assert "123456" in captured.out


# ── security.py production headers (lines 50-54) ─────────────────────────────

def test_production_security_headers(client: TestClient):
    with patch("backend.security.ENV", "production"):
        r = client.get("/health")
    assert r.status_code == 200
    assert "Strict-Transport-Security" in r.headers
    assert "Content-Security-Policy" in r.headers


# ── crud.py UserService (lines 109-112, 116) ──────────────────────────────────

def test_user_service_get_by_id_not_found(session):
    with pytest.raises(Exception) as exc_info:
        UserService.get_by_id(session, 999999)
    assert "404" in str(exc_info.value.status_code)


def test_user_service_list_users(client: TestClient, session):
    register_and_login(client, "alice", "alice@test.com")
    users = UserService.list_users(session)
    assert len(users) >= 1


# ── database.py get_session (lines 24-25) ────────────────────────────────────

def test_get_session_yields_session():
    from backend.database import get_session
    gen = get_session()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass


# ── dependencies.py uncovered branches ────────────────────────────────────────

def test_get_current_user_deleted_user(client: TestClient, session):
    """Token valid but user deleted — should return 401."""
    token = register_and_login(client, "ghost", "ghost@test.com")
    user = session.exec(select(User).where(User.email == "ghost@test.com")).first()
    session.delete(user)
    session.commit()
    r = client.get("/auth/me", headers=auth(token))
    assert r.status_code == 401


def test_get_temp_token_no_credentials(client: TestClient):
    """2FA verify called with no token."""
    r = client.post("/auth/2fa/verify", json={"code": "123456"})
    assert r.status_code == 401


def test_get_temp_token_invalid_token(client: TestClient):
    """2FA verify called with a bad token."""
    r = client.post("/auth/2fa/verify", json={"code": "123456"},
                    headers={"Authorization": "Bearer not.a.valid.token"})
    assert r.status_code == 401


def test_get_temp_token_rejects_full_access_token(client: TestClient):
    """Full JWT rejected on 2FA endpoint — scope != '2fa'."""
    token = register_and_login(client, "bob", "bob@test.com")
    r = client.post("/auth/2fa/verify", json={"code": "123456"}, headers=auth(token))
    assert r.status_code == 401


# ── main.py: register with OAuth email (lines 154-165) ───────────────────────

def test_register_with_google_oauth_email(client: TestClient, session):
    """Regular OAuth email (Google) — generic social login message."""
    user = User(
        username="guser",
        email="google@example.com",
        hashed_password=hash_password("oauth_google@example.com"),
    )
    session.add(user); session.commit()
    r = client.post("/auth/register", json={
        "username": "newguy2", "email": "google@example.com", "password": "TestPass1!",
    })
    assert r.status_code == 409
    assert "social" in r.json()["detail"].lower()


def test_register_duplicate_username_different_email(client: TestClient):
    register_and_login(client, "alice", "alice@test.com")
    r = client.post("/auth/register", json={
        "username": "alice", "email": "other@test.com", "password": "TestPass1!",
    })
    assert r.status_code == 409
    assert "username" in r.json()["detail"].lower()


# ── main.py: login with OAuth account (line 191) ─────────────────────────────

def test_login_password_rejected_for_oauth_account(client: TestClient, session):
    user = User(
        username="oauthuser",
        email="oauth@example.com",
        hashed_password=hash_password("oauth_oauth@example.com"),
    )
    session.add(user); session.commit()
    r = client.post("/auth/login", json={"email": "oauth@example.com", "password": "TestPass1!"})
    assert r.status_code == 401
    assert "social login" in r.json()["detail"].lower()


# ── main.py: self_update_role blocked for admin/manager (lines 256-262) ──────

def test_admin_cannot_self_update_role(client: TestClient, session):
    token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    r = client.patch("/auth/me/role", json={"role": "viewer"}, headers=auth(token))
    assert r.status_code == 403


def test_manager_cannot_self_update_role(client: TestClient, session):
    token = register_and_login(client, "mgr", "mgr@test.com")
    from sqlmodel import select
    user = session.exec(select(User).where(User.email == "mgr@test.com")).first()
    user.role = UserRole.manager
    session.add(user); session.commit()
    r = client.patch("/auth/me/role", json={"role": "viewer"}, headers=auth(token))
    assert r.status_code == 403


# ── main.py: analyze edge cases (lines 560-572) ──────────────────────────────

def test_analyze_wrong_content_type(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post("/api/analyze",
                    files={"file": ("test.txt", b"hello", "text/plain")},
                    headers=auth(token))
    assert r.status_code == 400


def test_analyze_empty_file(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post("/api/analyze",
                    files={"file": ("test.png", b"", "image/png")},
                    headers=auth(token))
    assert r.status_code == 400


def test_analyze_invalid_image_bytes(client: TestClient):
    """Content-Type says image but magic bytes are wrong."""
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post("/api/analyze",
                    files={"file": ("test.png", b"not an image at all", "image/png")},
                    headers=auth(token))
    assert r.status_code == 400


# ── main.py: file serving (lines 714-721) ────────────────────────────────────

def test_file_path_traversal_rejected(client: TestClient):
    r = client.get("/files/../backend/config.py")
    assert r.status_code in (400, 404)


def test_file_not_found(client: TestClient):
    r = client.get("/files/nonexistent_file.png")
    assert r.status_code == 404


# ── main.py: admin create admin clash (line 749) ─────────────────────────────

def test_admin_create_admin_duplicate_email(client: TestClient, session):
    mgr_token = register_and_login(client, "mgr", "mgr@test.com")
    user = session.exec(select(User).where(User.email == "mgr@test.com")).first()
    user.role = UserRole.manager
    session.add(user); session.commit()
    # First creation succeeds
    client.post("/admin/users", json={
        "username": "newadmin", "email": "newadmin@test.com", "password": "TestPass1!"
    }, headers=auth(mgr_token))
    # Second with same email fails
    r = client.post("/admin/users", json={
        "username": "newadmin2", "email": "newadmin@test.com", "password": "TestPass1!"
    }, headers=auth(mgr_token))
    assert r.status_code == 409


# ── main.py: admin update role user not found (line 772) ─────────────────────

def test_admin_update_role_user_not_found(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    r = client.patch("/admin/users/999999/role",
                     json={"role": "viewer"}, headers=auth(admin_token))
    assert r.status_code == 404


# ── main.py: admin assign admin role by non-manager (line 783) ───────────────

def test_admin_cannot_assign_admin_role(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    viewer = client.post("/auth/register", json={
        "username": "viewer1", "email": "viewer1@test.com", "password": "TestPass1!",
    }).json()
    r = client.patch(f"/admin/users/{viewer['id']}/role",
                     json={"role": "admin"}, headers=auth(admin_token))
    assert r.status_code == 403


# ── main.py: admin delete user not found (line 801) ──────────────────────────

def test_admin_delete_user_not_found(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    r = client.delete("/admin/users/999999", headers=auth(admin_token))
    assert r.status_code == 404


# ── main.py: _oauth_upsert_redirect (lines 522-547) ──────────────────────────

def test_oauth_upsert_no_email(client: TestClient, session):
    """OAuth callback with empty email redirects to error page."""
    from backend.main import _oauth_upsert_redirect
    response = _oauth_upsert_redirect(session, "", "Some User")
    assert "oauth_no_email" in response.headers["location"]


def test_oauth_upsert_password_account_redirects_to_error(client: TestClient, session):
    """OAuth with email that belongs to a password account — blocked."""
    register_and_login(client, "pwuser", "pwuser@test.com")
    from backend.main import _oauth_upsert_redirect
    response = _oauth_upsert_redirect(session, "pwuser@test.com", "PW User")
    assert "email_password_account" in response.headers["location"]


def test_oauth_upsert_username_collision_resolved(client: TestClient, session):
    """When display_name conflicts with existing username, a suffix is added."""
    register_and_login(client, "alice", "alice@test.com")
    from backend.main import _oauth_upsert_redirect
    # "alice" already taken — should create "alice1"
    response = _oauth_upsert_redirect(session, "new@test.com", "alice")
    assert "oauth-callback" in response.headers["location"]
    new_user = session.exec(select(User).where(User.email == "new@test.com")).first()
    assert new_user is not None
    assert new_user.username.startswith("alice")


def test_oauth_upsert_existing_oauth_user_logs_in(client: TestClient, session):
    """Existing OAuth account via same provider — logs in without error."""
    user = User(
        username="oauthlogin",
        email="oauthlogin@test.com",
        hashed_password=hash_password("oauth_oauthlogin@test.com"),
    )
    session.add(user); session.commit()
    from backend.main import _oauth_upsert_redirect
    response = _oauth_upsert_redirect(session, "oauthlogin@test.com", "OAuth Login")
    assert "oauth-callback" in response.headers["location"]
