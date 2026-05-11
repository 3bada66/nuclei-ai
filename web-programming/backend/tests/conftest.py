"""Shared fixtures for backend unit tests.

Heavy ML dependencies (torch, segmentation_models_pytorch, src.*) are mocked
at module level — before any backend code is imported — so tests run without
the full ML stack installed.
"""

import sys
import uuid
from unittest.mock import MagicMock

# ── Mock ML/src modules before any backend import ─────────────────────────────
_stub = MagicMock()
for _mod in (
    "src", "src.infer", "src.batch_count_refined",
    "torch", "torchvision", "segmentation_models_pytorch",
):
    sys.modules.setdefault(_mod, _stub)

# ── Real imports (after mocking) ──────────────────────────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.database import get_session
from backend.main import app
from backend.services.analysis_service import AnalysisResult


def _fake_result(filename: str = "test.png") -> AnalysisResult:
    jid = uuid.uuid4().hex[:12]
    return AnalysisResult(
        job_id=jid,
        status="ok-fallback",
        message="Test.",
        cell_count=42,
        input_url=f"/files/{jid}_input.png",
        mask_url=f"/files/{jid}_mask.png",
        overlay_url=f"/files/{jid}_overlay.png",
        metadata={
            "original_filename": filename,
            "mode": "fallback-demo",
            "threshold": None,
            "min_area": 20,
            "image_size": 256,
            "processing_ms": 50,
            "device": "cpu",
        },
    )


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def bypass_rate_limits(monkeypatch):
    """Disable slowapi rate limiting for all tests.

    _check_request_limit is replaced with a no-op that still writes the
    view_rate_limit state attribute slowapi reads when injecting headers.
    """
    from backend import main

    def _no_limit(request, *args, **kwargs):
        try:
            request.state.view_rate_limit = (None, None)
        except Exception:  # noqa: BLE001
            pass

    monkeypatch.setattr(main.limiter, "_check_request_limit", _no_limit)


@pytest.fixture(name="client")
def client_fixture(session: Session, monkeypatch):
    from backend.services import analysis_service

    monkeypatch.setattr(analysis_service, "_ensure_model_loaded", lambda: None)
    monkeypatch.setattr(
        analysis_service, "analyze",
        lambda image_bytes, original_filename: _fake_result(original_filename),
    )
    monkeypatch.setattr(
        analysis_service, "get_health",
        lambda: {"status": "ok", "device": "cpu", "model_loaded": False,
                 "mode": "fallback-demo", "load_error": None},
    )
    monkeypatch.setattr(
        analysis_service, "result_to_dict",
        lambda r: r.__dict__,
    )

    def override():
        yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helper: register + login, return token ────────────────────────────────────

def register_and_login(client: TestClient, username: str, email: str,
                       password: str = "TestPass1!") -> str:
    client.post("/auth/register", json={
        "username": username, "email": email, "password": password,
    })
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def make_admin(session, email: str) -> None:
    """Promote a registered user to admin directly via the DB."""
    from sqlmodel import select
    from backend.models import User, UserRole
    user = session.exec(select(User).where(User.email == email)).first()
    user.role = UserRole.admin
    session.add(user)
    session.commit()


def register_and_login_as_admin(client: TestClient, session, username: str,
                                email: str, password: str = "TestPass1!") -> str:
    """Register, promote to admin, then login. Returns token."""
    token = register_and_login(client, username, email, password)
    make_admin(session, email)
    return token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
