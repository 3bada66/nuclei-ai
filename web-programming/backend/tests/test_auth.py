"""Auth endpoint tests: register, login, me, error messages."""

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import auth, register_and_login


def test_register_success(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "TestPass1!",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@test.com"
    assert "hashed_password" not in data


def test_all_new_users_become_viewer(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "first", "email": "first@test.com", "password": "TestPass1!",
    })
    assert r.json()["role"] == "viewer"


def test_second_user_also_viewer(client: TestClient):
    client.post("/auth/register", json={
        "username": "first", "email": "first@test.com", "password": "TestPass1!",
    })
    r = client.post("/auth/register", json={
        "username": "second", "email": "second@test.com", "password": "TestPass1!",
    })
    assert r.json()["role"] == "viewer"


def test_register_duplicate_email(client: TestClient):
    client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "TestPass1!",
    })
    r = client.post("/auth/register", json={
        "username": "alice2", "email": "alice@test.com", "password": "TestPass1!",
    })
    assert r.status_code == 409


def test_register_duplicate_username(client: TestClient):
    client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "TestPass1!",
    })
    r = client.post("/auth/register", json={
        "username": "alice", "email": "other@test.com", "password": "TestPass1!",
    })
    assert r.status_code == 409


def test_login_success(client: TestClient):
    client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "TestPass1!",
    })
    r = client.post("/auth/login", json={"email": "alice@test.com", "password": "TestPass1!"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "alice"


def test_login_wrong_password(client: TestClient):
    client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "TestPass1!",
    })
    r = client.post("/auth/login", json={"email": "alice@test.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_nonexistent_email(client: TestClient):
    r = client.post("/auth/login", json={"email": "nobody@test.com", "password": "TestPass1!"})
    assert r.status_code == 401


def test_login_identical_error_for_wrong_email_and_wrong_password(client: TestClient):
    """Rule 9: same detail regardless of which credential is wrong."""
    client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "TestPass1!",
    })
    r_wrong_pass = client.post("/auth/login", json={
        "email": "alice@test.com", "password": "badpass",
    })
    r_wrong_email = client.post("/auth/login", json={
        "email": "ghost@test.com", "password": "TestPass1!",
    })
    assert r_wrong_pass.json()["detail"] == r_wrong_email.json()["detail"]


def test_get_me_authenticated(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.get("/auth/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_get_me_unauthenticated(client: TestClient):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_get_me_invalid_token(client: TestClient):
    r = client.get("/auth/me", headers=auth("not.a.valid.token"))
    assert r.status_code == 401


def test_register_password_too_short(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "short",
    })
    assert r.status_code == 422


def test_register_invalid_email(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "alice", "email": "not-an-email", "password": "TestPass1!",
    })
    assert r.status_code == 422
