"""CRUD endpoint tests: jobs and annotations."""

import io
import struct
import zlib

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import auth, register_and_login


def _tiny_png() -> bytes:
    """Minimal valid 1×1 white PNG for upload tests."""
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\xff\xff"
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def _upload_job(client: TestClient, token: str) -> str:
    r = client.post(
        "/api/analyze",
        files={"file": ("test.png", io.BytesIO(_tiny_png()), "image/png")},
        headers=auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()["job_id"]


# ── Job tests ─────────────────────────────────────────────────────────────────

def test_analyze_creates_job(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post(
        "/api/analyze",
        files={"file": ("img.png", io.BytesIO(_tiny_png()), "image/png")},
        headers=auth(token),
    )
    assert r.status_code == 201
    body = r.json()
    assert "job_id" in body
    assert body["cell_count"] == 42


def test_analyze_requires_auth(client: TestClient):
    r = client.post(
        "/api/analyze",
        files={"file": ("img.png", io.BytesIO(_tiny_png()), "image/png")},
    )
    assert r.status_code == 401


def test_analyze_rejects_non_image(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.post(
        "/api/analyze",
        files={"file": ("doc.pdf", io.BytesIO(b"not an image"), "application/pdf")},
        headers=auth(token),
    )
    assert r.status_code == 400


def test_list_jobs_empty(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.get("/api/jobs", headers=auth(token))
    assert r.status_code == 200
    assert r.json() == []


def test_list_jobs_returns_own(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    _upload_job(client, token)
    r = client.get("/api/jobs", headers=auth(token))
    assert len(r.json()) == 1


def test_get_job_by_id(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    job_id = _upload_job(client, token)
    r = client.get(f"/api/jobs/{job_id}", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["job_id"] == job_id


def test_get_job_not_found(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.get("/api/jobs/doesnotexist", headers=auth(token))
    assert r.status_code == 404


def test_delete_job(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    job_id = _upload_job(client, token)
    r = client.delete(f"/api/jobs/{job_id}", headers=auth(token))
    assert r.status_code == 204
    assert client.get(f"/api/jobs/{job_id}", headers=auth(token)).status_code == 404


def test_delete_job_not_found(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.delete("/api/jobs/ghost12345", headers=auth(token))
    assert r.status_code == 404


# ── Annotation tests ──────────────────────────────────────────────────────────

def test_create_annotation(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    job_id = _upload_job(client, token)
    r = client.post(
        f"/api/jobs/{job_id}/annotations",
        json={"note": "Interesting cluster in the top-left."},
        headers=auth(token),
    )
    assert r.status_code == 201
    assert r.json()["note"] == "Interesting cluster in the top-left."


def test_list_annotations(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    job_id = _upload_job(client, token)
    client.post(f"/api/jobs/{job_id}/annotations", json={"note": "Note A"}, headers=auth(token))
    client.post(f"/api/jobs/{job_id}/annotations", json={"note": "Note B"}, headers=auth(token))
    r = client.get(f"/api/jobs/{job_id}/annotations", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_annotation(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    job_id = _upload_job(client, token)
    ann_id = client.post(
        f"/api/jobs/{job_id}/annotations", json={"note": "to delete"},
        headers=auth(token),
    ).json()["id"]
    r = client.delete(f"/api/annotations/{ann_id}", headers=auth(token))
    assert r.status_code == 204


def test_delete_annotation_not_found(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    r = client.delete("/api/annotations/99999", headers=auth(token))
    assert r.status_code == 404


def test_annotation_empty_note_rejected(client: TestClient):
    token = register_and_login(client, "alice", "alice@test.com")
    job_id = _upload_job(client, token)
    r = client.post(
        f"/api/jobs/{job_id}/annotations", json={"note": ""},
        headers=auth(token),
    )
    assert r.status_code == 422
