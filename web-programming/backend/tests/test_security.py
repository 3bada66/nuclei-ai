"""Security hardening tests."""

import io
import struct
import zlib

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import auth, register_and_login
from backend.security import is_valid_image_bytes


# ── Magic-bytes helper (reused from test_roles.py) ───────────────────────────

def _tiny_png() -> bytes:
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ── is_valid_image_bytes unit tests ──────────────────────────────────────────

def test_png_magic_accepted():
    assert is_valid_image_bytes(_tiny_png()) is True


def test_jpeg_magic_accepted():
    jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
    assert is_valid_image_bytes(jpeg_header) is True


def test_text_file_rejected():
    assert is_valid_image_bytes(b"hello world") is False


def test_empty_rejected():
    assert is_valid_image_bytes(b"") is False


def test_truncated_signature_rejected():
    # Only first 2 bytes of PNG sig — not enough to match
    assert is_valid_image_bytes(b"\x89P") is False


# ── Upload endpoint rejects non-image magic bytes ────────────────────────────

def test_analyze_rejects_disguised_text_as_image(client: TestClient):
    """A file with image content-type but non-image bytes must be rejected."""
    token = register_and_login(client, "sec1", "sec1@test.com")
    r = client.post(
        "/api/analyze",
        files={"file": ("evil.png", io.BytesIO(b"not an image"), "image/png")},
        headers=auth(token),
    )
    assert r.status_code == 400
    assert "image" in r.json()["detail"].lower()


def test_analyze_accepts_valid_png(client: TestClient):
    token = register_and_login(client, "sec2", "sec2@test.com")
    r = client.post(
        "/api/analyze",
        files={"file": ("t.png", io.BytesIO(_tiny_png()), "image/png")},
        headers=auth(token),
    )
    assert r.status_code == 201


# ── Security headers ──────────────────────────────────────────────────────────

def test_security_headers_present(client: TestClient):
    r = client.get("/api/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "permissions-policy" in r.headers


def test_content_security_policy_present(client: TestClient):
    r = client.get("/api/health")
    assert "content-security-policy" in r.headers


# ── Password strength validation ─────────────────────────────────────────────

def test_register_password_letters_only_rejected(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec3", "email": "sec3@test.com", "password": "abcdefgh",
    })
    assert r.status_code == 422


def test_register_password_digits_only_rejected(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec4", "email": "sec4@test.com", "password": "12345678",
    })
    assert r.status_code == 422


def test_register_password_mixed_accepted(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec5", "email": "sec5@test.com", "password": "TestPass1!",
    })
    assert r.status_code == 201


def test_register_password_no_uppercase_rejected(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec6", "email": "sec6@test.com", "password": "testpass1!",
    })
    assert r.status_code == 422


def test_register_password_no_special_rejected(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec7", "email": "sec7@test.com", "password": "TestPass123",
    })
    assert r.status_code == 422


def test_register_password_arabic_rejected(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec8", "email": "sec8@test.com", "password": "كلمة@123A",
    })
    assert r.status_code == 422


def test_register_password_space_rejected(client: TestClient):
    r = client.post("/auth/register", json={
        "username": "sec9", "email": "sec9@test.com", "password": "Obada 123@",
    })
    assert r.status_code == 422


# ── /health alias ─────────────────────────────────────────────────────────────

def test_health_alias_responds(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── /reset-db unavailable in production ──────────────────────────────────────

def test_reset_db_available_in_dev(client: TestClient):
    """In test environment (ENV=development) the endpoint must exist."""
    r = client.post("/reset-db")
    assert r.status_code == 200


# ── TOTP code is exactly 6 digits ────────────────────────────────────────────

def test_totp_verify_request_rejects_non_digit_code(client: TestClient):
    token = register_and_login(client, "sec6", "sec6@test.com")
    r = client.post("/auth/2fa/verify-setup", json={"code": "abcdef"}, headers=auth(token))
    assert r.status_code == 422


def test_totp_verify_request_rejects_short_code(client: TestClient):
    token = register_and_login(client, "sec7", "sec7@test.com")
    r = client.post("/auth/2fa/verify-setup", json={"code": "123"}, headers=auth(token))
    assert r.status_code == 422
