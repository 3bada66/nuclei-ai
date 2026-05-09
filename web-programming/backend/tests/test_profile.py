"""Tests for PATCH /auth/me (update profile) and POST /auth/change-password."""

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import auth, register_and_login


# ── PATCH /auth/me ─────────────────────────────────────────────────────────────

def test_update_username(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.patch("/auth/me", json={"username": "alice2"}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == "alice2"


def test_update_email(client: TestClient):
    token = register_and_login(client, "bob", "bob@test.com")
    r = client.patch("/auth/me", json={"email": "bob2@test.com"}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["email"] == "bob2@test.com"


def test_update_username_and_email(client: TestClient):
    token = register_and_login(client, "carol", "carol@test.com")
    r = client.patch("/auth/me", json={"username": "carol2", "email": "carol2@test.com"}, headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "carol2"
    assert data["email"] == "carol2@test.com"


def test_update_username_conflict(client: TestClient):
    register_and_login(client, "dave", "dave@test.com")
    token = register_and_login(client, "eve", "eve@test.com")
    r = client.patch("/auth/me", json={"username": "dave"}, headers=auth(token))
    assert r.status_code == 409


def test_update_email_conflict(client: TestClient):
    register_and_login(client, "frank", "frank@test.com")
    token = register_and_login(client, "grace", "grace@test.com")
    r = client.patch("/auth/me", json={"email": "frank@test.com"}, headers=auth(token))
    assert r.status_code == 409


def test_update_profile_requires_auth(client: TestClient):
    r = client.patch("/auth/me", json={"username": "hacker"})
    assert r.status_code == 401


def test_update_empty_body_ok(client: TestClient):
    token = register_and_login(client, "henry", "henry@test.com")
    r = client.patch("/auth/me", json={}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == "henry"


# ── POST /auth/change-password ─────────────────────────────────────────────────

def test_change_password_success(client: TestClient):
    token = register_and_login(client, "ivan", "ivan@test.com", "OldPass1!")
    r = client.post("/auth/change-password", json={
        "current_password": "OldPass1!",
        "new_password": "NewPass2@",
    }, headers=auth(token))
    assert r.status_code == 200

    # Can now log in with new password
    r2 = client.post("/auth/login", json={"email": "ivan@test.com", "password": "NewPass2@"})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_change_password_wrong_current(client: TestClient):
    token = register_and_login(client, "judy", "judy@test.com", "OldPass1!")
    r = client.post("/auth/change-password", json={
        "current_password": "wrongpassword",
        "new_password": "NewPass2@",
    }, headers=auth(token))
    assert r.status_code in (400, 401)


def test_change_password_weak_new(client: TestClient):
    token = register_and_login(client, "karl", "karl@test.com", "OldPass1!")
    r = client.post("/auth/change-password", json={
        "current_password": "OldPass1!",
        "new_password": "short",
    }, headers=auth(token))
    assert r.status_code == 422


def test_change_password_requires_auth(client: TestClient):
    r = client.post("/auth/change-password", json={
        "current_password": "OldPass1!",
        "new_password": "NewPass2@",
    })
    assert r.status_code == 401


def test_old_password_rejected_after_change(client: TestClient):
    register_and_login(client, "lena", "lena@test.com", "OldPass1!")
    token = register_and_login(client, "lena", "lena@test.com", "OldPass1!")
    client.post("/auth/change-password", json={
        "current_password": "OldPass1!",
        "new_password": "NewPass2@",
    }, headers=auth(token))

    r = client.post("/auth/login", json={"email": "lena@test.com", "password": "OldPass1!"})
    assert r.status_code == 401
