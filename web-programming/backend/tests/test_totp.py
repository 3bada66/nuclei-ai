"""TOTP 2FA flow tests."""

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import auth, register_and_login
from backend.totp_utils import generate_totp_secret, verify_totp
import pyotp


def test_totp_setup_returns_secret_and_uri(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post("/auth/2fa/setup", headers=auth(token))
    assert r.status_code == 200
    body = r.json()
    assert "secret" in body
    assert "uri" in body
    assert "otpauth://" in body["uri"]


def test_totp_setup_requires_auth(client: TestClient):
    r = client.post("/auth/2fa/setup")
    assert r.status_code == 401


def test_totp_verify_setup_correct_code(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    setup_r = client.post("/auth/2fa/setup", headers=auth(token))
    secret = setup_r.json()["secret"]
    code = pyotp.TOTP(secret).now()

    r = client.post("/auth/2fa/verify-setup", json={"code": code}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_totp_verify_setup_wrong_code(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    client.post("/auth/2fa/setup", headers=auth(token))
    r = client.post("/auth/2fa/verify-setup", json={"code": "000000"}, headers=auth(token))
    assert r.status_code == 400


def test_totp_verify_setup_without_setup_first(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post("/auth/2fa/verify-setup", json={"code": "123456"}, headers=auth(token))
    assert r.status_code == 400


def test_login_requires_2fa_when_totp_enabled(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    setup_r = client.post("/auth/2fa/setup", headers=auth(token))
    secret = setup_r.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post("/auth/2fa/verify-setup", json={"code": code}, headers=auth(token))

    login_r = client.post("/auth/login", json={"email": "alice@test.com", "password": "TestPass1!"})
    assert login_r.status_code == 200
    body = login_r.json()
    assert body.get("requires_2fa") is True
    assert "temp_token" in body
    assert "access_token" not in body


def test_totp_complete_login_flow(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    setup_r = client.post("/auth/2fa/setup", headers=auth(token))
    secret = setup_r.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post("/auth/2fa/verify-setup", json={"code": code}, headers=auth(token))

    # Step 1: login returns temp token
    login_r = client.post("/auth/login", json={"email": "alice@test.com", "password": "TestPass1!"})
    temp_token = login_r.json()["temp_token"]

    # Step 2: verify TOTP with temp token → full access token
    fresh_code = pyotp.TOTP(secret).now()
    verify_r = client.post(
        "/auth/2fa/verify",
        json={"code": fresh_code},
        headers=auth(temp_token),
    )
    assert verify_r.status_code == 200
    assert "access_token" in verify_r.json()


def test_totp_verify_with_wrong_code(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    setup_r = client.post("/auth/2fa/setup", headers=auth(token))
    secret = setup_r.json()["secret"]
    good_code = pyotp.TOTP(secret).now()
    client.post("/auth/2fa/verify-setup", json={"code": good_code}, headers=auth(token))

    login_r = client.post("/auth/login", json={"email": "alice@test.com", "password": "TestPass1!"})
    temp_token = login_r.json()["temp_token"]

    r = client.post("/auth/2fa/verify", json={"code": "000000"}, headers=auth(temp_token))
    assert r.status_code == 401


def test_full_access_token_rejected_on_2fa_verify_endpoint(client: TestClient):
    """Regular JWT cannot be used in the 2FA verify endpoint (scope check)."""
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post("/auth/2fa/verify", json={"code": "123456"}, headers=auth(token))
    assert r.status_code == 401


def test_temp_token_rejected_on_protected_endpoints(client: TestClient):
    """Temp 2FA token (scope=2fa) cannot access /auth/me or other protected routes."""
    token = register_and_login(client, "alice", "alice@test.com")
    setup_r = client.post("/auth/2fa/setup", headers=auth(token))
    secret = setup_r.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post("/auth/2fa/verify-setup", json={"code": code}, headers=auth(token))

    login_r = client.post("/auth/login", json={"email": "alice@test.com", "password": "TestPass1!"})
    temp_token = login_r.json()["temp_token"]

    r = client.get("/auth/me", headers=auth(temp_token))
    assert r.status_code == 401
