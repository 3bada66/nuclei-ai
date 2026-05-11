"""Role-based access control tests — 4-tier hierarchy: manager > admin > researcher > viewer."""

import io
import struct
import zlib

from fastapi.testclient import TestClient
from sqlmodel import select

from backend.models import User, UserRole
from backend.tests.conftest import auth, register_and_login, register_and_login_as_admin


# ── Helpers ───────────────────────────────────────────────────────────────────

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
        files={"file": ("t.png", io.BytesIO(_tiny_png()), "image/png")},
        headers=auth(token),
    )
    assert r.status_code == 201
    return r.json()["job_id"]


def _promote(session, email: str, role: UserRole):
    """Directly promote a user in the test DB."""
    user = session.exec(select(User).where(User.email == email)).first()
    user.role = role
    session.add(user)
    session.commit()



# ── Jobs visibility ───────────────────────────────────────────────────────────

def test_admin_sees_all_jobs(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    viewer_token = register_and_login(client, "viewer", "viewer@test.com")
    _upload(client, admin_token)
    _upload(client, viewer_token)
    r = client.get("/api/jobs", headers=auth(admin_token))
    assert len(r.json()) == 2


def test_viewer_sees_only_own_jobs(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    viewer_token = register_and_login(client, "viewer", "viewer@test.com")
    _upload(client, admin_token)
    _upload(client, viewer_token)
    r = client.get("/api/jobs", headers=auth(viewer_token))
    assert len(r.json()) == 1


def test_viewer_cannot_access_others_job(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    viewer_token = register_and_login(client, "viewer", "viewer@test.com")
    admin_job_id = _upload(client, admin_token)
    r = client.get(f"/api/jobs/{admin_job_id}", headers=auth(viewer_token))
    assert r.status_code == 403


# ── Admin page access control ─────────────────────────────────────────────────

def test_viewer_blocked_from_admin_list(client: TestClient):
    viewer_token = register_and_login(client, "viewer", "viewer@test.com")
    assert client.get("/admin/users", headers=auth(viewer_token)).status_code == 403


def test_researcher_blocked_from_admin_list(client: TestClient, session):
    r_token = register_and_login(client, "res", "res@test.com")
    _promote(session, "res@test.com", UserRole.researcher)
    assert client.get("/admin/users", headers=auth(r_token)).status_code == 403


def test_viewer_blocked_from_admin_stats(client: TestClient):
    viewer_token = register_and_login(client, "viewer", "viewer@test.com")
    assert client.get("/admin/stats", headers=auth(viewer_token)).status_code == 403


def test_unauthenticated_blocked_from_admin(client: TestClient):
    assert client.get("/admin/users").status_code == 401


# ── 1. Manager can access admin page ─────────────────────────────────────────

def test_manager_can_access_admin_page(client: TestClient, session):
    mgr_token = register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    assert client.get("/admin/users", headers=auth(mgr_token)).status_code == 200
    assert client.get("/admin/stats", headers=auth(mgr_token)).status_code == 200


# ── 2. Manager can add a new admin ────────────────────────────────────────────

def test_manager_can_create_admin(client: TestClient, session):
    mgr_token = register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    r = client.post("/admin/users", json={
        "username": "newadmin", "email": "newadmin@test.com", "password": "TestPass1!",
    }, headers=auth(mgr_token))
    assert r.status_code == 201
    assert r.json()["role"] == "admin"


def test_admin_cannot_create_admin(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    r = client.post("/admin/users", json={
        "username": "newadmin", "email": "newadmin@test.com", "password": "TestPass1!",
    }, headers=auth(admin_token))
    assert r.status_code == 403


def test_viewer_cannot_create_admin(client: TestClient):
    viewer_token = register_and_login(client, "viewer", "viewer@test.com")
    r = client.post("/admin/users", json={
        "username": "newadmin", "email": "newadmin@test.com", "password": "TestPass1!",
    }, headers=auth(viewer_token))
    assert r.status_code == 403


# ── 3 & 4. Manager can change viewer↔researcher ───────────────────────────────

def test_manager_can_change_viewer_to_researcher(client: TestClient, session):
    mgr_token = register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    viewer = client.post("/auth/register", json={
        "username": "view1", "email": "view1@test.com", "password": "TestPass1!",
    }).json()
    r = client.patch(f"/admin/users/{viewer['id']}/role",
                     json={"role": "researcher"}, headers=auth(mgr_token))
    assert r.status_code == 200
    assert r.json()["role"] == "researcher"


def test_manager_can_change_researcher_to_viewer(client: TestClient, session):
    mgr_token = register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    res = client.post("/auth/register", json={
        "username": "res1", "email": "res1@test.com", "password": "TestPass1!",
    }).json()
    _promote(session, "res1@test.com", UserRole.researcher)
    r = client.patch(f"/admin/users/{res['id']}/role",
                     json={"role": "viewer"}, headers=auth(mgr_token))
    assert r.status_code == 200
    assert r.json()["role"] == "viewer"


# ── 5. Admin can access admin page ────────────────────────────────────────────

def test_admin_can_access_admin_page(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    assert client.get("/admin/users", headers=auth(admin_token)).status_code == 200


def test_admin_can_list_users(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    register_and_login(client, "bob", "bob@test.com")
    r = client.get("/admin/users", headers=auth(admin_token))
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── 6. Admin can change viewer/researcher roles only ─────────────────────────

def test_admin_can_change_viewer_to_researcher(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    viewer = client.post("/auth/register", json={
        "username": "view1", "email": "view1@test.com", "password": "TestPass1!",
    }).json()
    r = client.patch(f"/admin/users/{viewer['id']}/role",
                     json={"role": "researcher"}, headers=auth(admin_token))
    assert r.status_code == 200
    assert r.json()["role"] == "researcher"


# ── 7. Admin cannot add another admin ────────────────────────────────────────
# (tested above in test_admin_cannot_create_admin)

# ── 8. Admin cannot edit/remove another admin ─────────────────────────────────

def test_admin_cannot_change_another_admins_role(client: TestClient, session):
    admin_token = register_and_login(client, "admin1", "admin1@test.com")
    register_and_login(client, "admin2", "admin2@test.com")
    admin2 = session.exec(select(User).where(User.email == "admin2@test.com")).first()
    admin2.role = UserRole.admin
    session.add(admin2); session.commit()
    r = client.patch(f"/admin/users/{admin2.id}/role",
                     json={"role": "viewer"}, headers=auth(admin_token))
    assert r.status_code == 403


def test_admin_cannot_delete_another_admin(client: TestClient, session):
    admin_token = register_and_login(client, "admin1", "admin1@test.com")
    register_and_login(client, "admin2", "admin2@test.com")
    admin2 = session.exec(select(User).where(User.email == "admin2@test.com")).first()
    admin2.role = UserRole.admin
    session.add(admin2); session.commit()
    r = client.delete(f"/admin/users/{admin2.id}", headers=auth(admin_token))
    assert r.status_code == 403


# ── 9. Admin cannot edit/remove manager ──────────────────────────────────────

def test_admin_cannot_change_manager_role(client: TestClient, session):
    admin_token = register_and_login(client, "admin", "admin@test.com")
    register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    mgr = session.exec(select(User).where(User.email == "mgr@test.com")).first()
    r = client.patch(f"/admin/users/{mgr.id}/role",
                     json={"role": "viewer"}, headers=auth(admin_token))
    assert r.status_code == 403


def test_admin_cannot_delete_manager(client: TestClient, session):
    admin_token = register_and_login(client, "admin", "admin@test.com")
    register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    mgr = session.exec(select(User).where(User.email == "mgr@test.com")).first()
    r = client.delete(f"/admin/users/{mgr.id}", headers=auth(admin_token))
    assert r.status_code == 403


# ── 10 & 11. Viewer/researcher cannot see admin page ─────────────────────────
# (tested above)

# ── 12. Direct API access blocked ────────────────────────────────────────────

def test_viewer_direct_api_blocked(client: TestClient):
    register_and_login(client, "admin", "admin@test.com")
    viewer_token = register_and_login(client, "view1", "view1@test.com")
    assert client.get("/admin/users", headers=auth(viewer_token)).status_code == 403
    assert client.get("/admin/stats", headers=auth(viewer_token)).status_code == 403


# ── 13. Nobody can create manager via API ────────────────────────────────────

def test_cannot_promote_to_manager_via_role_change(client: TestClient, session):
    """RoleUpdateRequest only allows viewer/researcher — manager is rejected by schema."""
    mgr_token = register_and_login(client, "mgr", "mgr@test.com")
    _promote(session, "mgr@test.com", UserRole.manager)
    viewer = client.post("/auth/register", json={
        "username": "view1", "email": "view1@test.com", "password": "TestPass1!",
    }).json()
    r = client.patch(f"/admin/users/{viewer['id']}/role",
                     json={"role": "manager"}, headers=auth(mgr_token))
    assert r.status_code == 422   # schema rejects "manager" as a role value


def test_cannot_register_as_manager(client: TestClient):
    """Register endpoint always assigns viewer (or admin for first user). Never manager."""
    r = client.post("/auth/register", json={
        "username": "hack", "email": "hack@test.com", "password": "TestPass1!",
    })
    assert r.status_code in (201, 409)
    if r.status_code == 201:
        assert r.json()["role"] != "manager"


# ── 14. Nobody can change own role ────────────────────────────────────────────

def test_nobody_can_change_own_role(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    me = client.get("/auth/me", headers=auth(admin_token)).json()
    r = client.patch(f"/admin/users/{me['id']}/role",
                     json={"role": "viewer"}, headers=auth(admin_token))
    assert r.status_code == 400


# ── Existing tests preserved ──────────────────────────────────────────────────

def test_admin_cannot_delete_themselves(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    me = client.get("/auth/me", headers=auth(admin_token)).json()
    r = client.delete(f"/admin/users/{me['id']}", headers=auth(admin_token))
    assert r.status_code == 400


def test_admin_can_delete_viewer(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    viewer = client.post("/auth/register", json={
        "username": "view1", "email": "view1@test.com", "password": "TestPass1!",
    }).json()
    r = client.delete(f"/admin/users/{viewer['id']}", headers=auth(admin_token))
    assert r.status_code == 204


def test_admin_stats(client: TestClient, session):
    admin_token = register_and_login_as_admin(client, session, "admin", "admin@test.com")
    r = client.get("/admin/stats", headers=auth(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert "total_users" in body
    assert "users_by_role" in body
    assert body["total_users"] == 1
    assert "manager" in body["users_by_role"]
    assert "admin" in body["users_by_role"]
