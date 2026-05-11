"""CSV export endpoint tests."""

import io
import struct
import zlib
import csv

from fastapi.testclient import TestClient
from backend.tests.conftest import auth, register_and_login, register_and_login_as_admin


def _tiny_png() -> bytes:
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def _upload(client: TestClient, token: str) -> str:
    r = client.post(
        "/api/analyze",
        files={"file": ("sample.png", io.BytesIO(_tiny_png()), "image/png")},
        headers=auth(token),
    )
    assert r.status_code == 201
    return r.json()["job_id"]


def test_export_requires_auth(client: TestClient):
    r = client.get("/api/jobs/export.csv")
    assert r.status_code == 401


def test_export_returns_csv_content_type(client: TestClient):
    token = register_and_login(client, "exp1", "exp1@test.com")
    r = client.get("/api/jobs/export.csv", headers=auth(token))
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_export_has_content_disposition(client: TestClient):
    token = register_and_login(client, "exp2", "exp2@test.com")
    r = client.get("/api/jobs/export.csv", headers=auth(token))
    assert "attachment" in r.headers.get("content-disposition", "")
    assert ".csv" in r.headers.get("content-disposition", "")


def test_export_empty_when_no_jobs(client: TestClient):
    token = register_and_login(client, "exp3", "exp3@test.com")
    r = client.get("/api/jobs/export.csv", headers=auth(token))
    assert r.status_code == 200
    lines = r.text.strip().splitlines()
    assert len(lines) == 1  # header row only


def test_export_contains_correct_headers(client: TestClient):
    token = register_and_login(client, "exp4", "exp4@test.com")
    r = client.get("/api/jobs/export.csv", headers=auth(token))
    reader = csv.reader(io.StringIO(r.text))
    header = next(reader)
    assert "job_id" in header
    assert "original_filename" in header
    assert "cell_count" in header
    assert "mode" in header
    assert "created_at" in header


def test_export_one_row_per_job(client: TestClient):
    token = register_and_login(client, "exp5", "exp5@test.com")
    _upload(client, token)
    _upload(client, token)

    r = client.get("/api/jobs/export.csv", headers=auth(token))
    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert len(rows) == 3  # header + 2 data rows


def test_viewer_exports_only_own_jobs(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "adm_exp", "adm_exp@test.com")
    viewer_token = register_and_login(client, "view_exp", "view_exp@test.com")

    _upload(client, admin_token)
    _upload(client, viewer_token)

    admin_r = client.get("/api/jobs/export.csv", headers=auth(admin_token))
    viewer_r = client.get("/api/jobs/export.csv", headers=auth(viewer_token))

    admin_rows = list(csv.reader(io.StringIO(admin_r.text)))
    viewer_rows = list(csv.reader(io.StringIO(viewer_r.text)))

    # admin sees 2 jobs (+ header), viewer sees 1 (+ header)
    assert len(admin_rows) == 3
    assert len(viewer_rows) == 2


def test_export_csv_values_match_job(client: TestClient):
    token = register_and_login(client, "exp6", "exp6@test.com")
    job_id = _upload(client, token)

    r = client.get("/api/jobs/export.csv", headers=auth(token))
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["job_id"] == job_id
    assert rows[0]["original_filename"] == "sample.png"
    assert int(rows[0]["cell_count"]) >= 0
