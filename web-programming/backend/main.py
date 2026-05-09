"""FastAPI entry point for the Nuclei Analysis API.

Run from the project root (web-programming/):
    uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
"""

import csv
import io
from contextlib import asynccontextmanager

import httpx
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Union

from fastapi import Body, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from jose import JWTError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import Session, SQLModel, select, text
from starlette.middleware.sessions import SessionMiddleware

from backend.auth_utils import (
    create_access_token,
    create_temp_token,
    decode_token,
    generate_otp,
    generate_reset_token,
    hash_otp,
    hash_password,
    send_otp_email,
    send_reset_code_email,
    verify_otp_hash,
    verify_password,
)
from backend.config import ENV, FRONTEND_URL, SECRET_KEY
from backend.security import SecurityHeadersMiddleware, is_valid_image_bytes
from backend.crud import AnnotationService, JobService
from backend.database import create_db_and_tables, engine, get_session
from backend.dependencies import get_current_user, get_temp_token_user_id, require_role
from backend.models import AnalysisJob, User, UserRole
from backend.oauth import oauth
from backend.schemas import (
    AnalysisResponse,
    AnnotationCreate,
    AnnotationResponse,
    ChangePasswordRequest,
    CreateAdminRequest,
    SelfRoleRequest,
    EmailOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
    EmailOTPVerifyRequest,
    HealthResponse,
    JobResponse,
    JobSummary,
    LoginRequest,
    RegisterRequest,
    RoleUpdateRequest,
    TokenResponse,
    TwoFactorRequiredResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UpdateProfileRequest,
    UserResponse,
)
from backend.services import analysis_service
from backend.totp_utils import generate_totp_secret, get_totp_uri, verify_totp

RESULT_DIR = Path(__file__).resolve().parent / "storage" / "results"

# Role groups used throughout admin logic
_ELEVATED = (UserRole.manager, UserRole.admin)       # can access admin endpoints
_MANAGEABLE = (UserRole.viewer, UserRole.researcher)  # roles that can be changed via dropdown


# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    analysis_service._ensure_model_loaded()
    yield


# ── App ───────────────────────────────────────────────────────────────────────

_docs_url = None if ENV == "production" else "/docs"
_redoc_url = None if ENV == "production" else "/redoc"

app = FastAPI(
    title="Nuclei Analysis API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers — added first so they apply to every response
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS: only allow localhost origins in development
_cors_origins = [FRONTEND_URL]
if ENV != "production":
    _cors_origins += ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**analysis_service.get_health())


# ── Auth: Register / Login / Me ───────────────────────────────────────────────

@app.post("/auth/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: RegisterRequest = Body(...),
    session: Session = Depends(get_session),
) -> UserResponse:
    existing = session.exec(
        select(User).where((User.email == data.email) | (User.username == data.username))
    ).first()
    if existing:
        if existing.email == data.email:
            # Detect OAuth-only accounts: their password is hash_password(f"oauth_{email}")
            if verify_password(f"oauth_{data.email}", existing.hashed_password):
                raise HTTPException(
                    status_code=409,
                    detail="This email is already linked to a social login. Please sign in with Google, GitHub, or Dropbox instead."
                )
            raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.")
        raise HTTPException(status_code=409, detail="This username is already taken.")
    is_first_user = session.exec(select(User)).first() is None
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.admin if is_first_user else UserRole.viewer,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse.model_validate(user)


@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest = Body(...),
    session: Session = Depends(get_session),
) -> Union[TokenResponse, TwoFactorRequiredResponse]:
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    # Detect OAuth-only accounts trying to log in with password
    if verify_password(f"oauth_{data.email}", user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="This account uses social login. Please sign in with Google, GitHub, or Dropbox."
        )
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if user.totp_enabled:
        return TwoFactorRequiredResponse(temp_token=create_temp_token(user.id))

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@app.patch("/auth/me", response_model=UserResponse)
def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    if data.username is not None and data.username != current_user.username:
        clash = session.exec(select(User).where(User.username == data.username)).first()
        if clash:
            raise HTTPException(status_code=409, detail="Username already taken.")
        current_user.username = data.username
    if data.email is not None and data.email != current_user.email:
        clash = session.exec(select(User).where(User.email == data.email)).first()
        if clash:
            raise HTTPException(status_code=409, detail="Email already registered.")
        current_user.email = data.email
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return UserResponse.model_validate(current_user)


@app.post("/auth/change-password", response_model=UserResponse)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: ChangePasswordRequest = Body(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    current_user.hashed_password = hash_password(data.new_password)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return UserResponse.model_validate(current_user)


@app.patch("/auth/me/role", response_model=UserResponse)
def self_update_role(
    data: SelfRoleRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    """Viewer/researcher can switch their own role between viewer and researcher."""
    if current_user.role not in _MANAGEABLE:
        raise HTTPException(status_code=403, detail="Only viewers and researchers can change their own role.")
    current_user.role = UserRole(data.role)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return UserResponse.model_validate(current_user)


# ── Auth: Forgot / Reset Password ────────────────────────────────────────────

# Prefix stored in reset_token_hash during the code phase.
# Prevents raw 6-digit codes from being accepted by /auth/reset-password.
_RESET_CODE_PREFIX = "RESET_CODE:"


@app.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest = Body(...),
    session: Session = Depends(get_session),
) -> dict:
    user = session.exec(select(User).where(User.email == data.email)).first()
    # Always return the same message — never reveal whether email exists
    if user:
        code = generate_otp()   # 6-digit code, same generator as login OTP
        # Store prefixed hash so /auth/reset-password cannot accept this hash directly
        user.reset_token_hash = _RESET_CODE_PREFIX + hash_otp(code)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        session.add(user)
        session.commit()
        send_reset_code_email(user.email, code)
    return {"message": "If that email exists, a verification code was sent."}


@app.post("/auth/verify-reset-code", response_model=VerifyResetCodeResponse)
@limiter.limit("5/minute")
async def verify_reset_code(
    request: Request,
    data: VerifyResetCodeRequest = Body(...),
    session: Session = Depends(get_session),
) -> VerifyResetCodeResponse:
    """Validate the 6-digit reset code.

    Returns a short-lived reset_token. This is NOT a login token — it has no
    auth scope, is never stored in the auth context, and only works with
    /auth/reset-password.
    """
    user = session.exec(select(User).where(User.email == data.email)).first()
    now = datetime.now(timezone.utc)
    stored = user.reset_token_hash if user else None
    valid = (
        user is not None
        and stored is not None
        and stored.startswith(_RESET_CODE_PREFIX)
        and user.reset_token_expires_at is not None
        and user.reset_token_expires_at.replace(tzinfo=timezone.utc) > now
        and stored == _RESET_CODE_PREFIX + hash_otp(data.code)
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Code is invalid or has expired.")
    # Code accepted — replace with a short-lived reset token (no prefix = accepted by /reset-password)
    reset_token = generate_reset_token()
    user.reset_token_hash = hash_otp(reset_token)   # type: ignore[union-attr]
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    session.add(user)
    session.commit()
    return VerifyResetCodeResponse(reset_token=reset_token)


@app.post("/auth/reset-password")
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    data: ResetPasswordRequest = Body(...),
    session: Session = Depends(get_session),
) -> dict:
    token_hash = hash_otp(data.token)
    user = session.exec(
        select(User).where(User.reset_token_hash == token_hash)
    ).first()
    now = datetime.now(timezone.utc)
    # Reject if not found, expired, or still in code phase (prefixed hash won't match)
    if (
        not user
        or not user.reset_token_expires_at
        or user.reset_token_expires_at.replace(tzinfo=timezone.utc) < now
    ):
        raise HTTPException(status_code=400, detail="Reset token is invalid or has expired.")
    user.hashed_password = hash_password(data.new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    session.add(user)
    session.commit()
    return {"message": "Password reset successfully. Please log in with your new password."}


# ── Auth: TOTP 2FA ────────────────────────────────────────────────────────────

@app.post("/auth/2fa/setup", response_model=TwoFactorSetupResponse)
def totp_setup(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TwoFactorSetupResponse:
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    session.add(current_user)
    session.commit()
    return TwoFactorSetupResponse(
        secret=secret,
        uri=get_totp_uri(secret, current_user.email),
    )


@app.post("/auth/2fa/verify-setup", response_model=UserResponse)
def totp_verify_setup(
    data: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Call /auth/2fa/setup first.")
    if not verify_totp(current_user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code.")
    current_user.totp_enabled = True
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return UserResponse.model_validate(current_user)


@app.post("/auth/2fa/verify", response_model=TokenResponse)
def totp_verify(
    data: TwoFactorVerifyRequest,
    user_id: int = Depends(get_temp_token_user_id),
    session: Session = Depends(get_session),
) -> TokenResponse:
    user = session.get(User, user_id)
    if not user or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Invalid session.")
    if not verify_totp(user.totp_secret, data.code):
        raise HTTPException(status_code=401, detail="Invalid TOTP code.")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ── Auth: Email OTP ───────────────────────────────────────────────────────────

@app.post("/auth/email-otp/send")
@limiter.limit("3/minute")
async def email_otp_send(
    request: Request,
    data: EmailOTPRequest = Body(...),
    session: Session = Depends(get_session),
) -> dict:
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    code = generate_otp()
    user.email_otp_hash = hash_otp(code)
    user.email_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    session.add(user)
    session.commit()
    send_otp_email(user.email, code)
    return {"message": "A verification code was sent to your email."}


@app.post("/auth/email-otp/verify", response_model=TokenResponse)
@limiter.limit("5/minute")
async def email_otp_verify(
    request: Request,
    data: EmailOTPVerifyRequest = Body(...),
    session: Session = Depends(get_session),
) -> TokenResponse:
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    now = datetime.now(timezone.utc)
    if (
        not user.email_otp_hash
        or not user.email_otp_expires_at
        or user.email_otp_expires_at.replace(tzinfo=timezone.utc) < now
        or not verify_otp_hash(data.code, user.email_otp_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid or expired code.")
    # Invalidate OTP after use
    user.email_otp_hash = None
    user.email_otp_expires_at = None
    session.add(user)
    session.commit()
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ── Auth: Google OAuth ────────────────────────────────────────────────────────

@app.get("/auth/google")
async def google_login(request: Request):
    if not hasattr(oauth, "google"):
        raise HTTPException(status_code=501, detail="Google OAuth not configured.")
    redirect_uri = str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback", name="google_callback")
async def google_callback(request: Request, session: Session = Depends(get_session)):
    if not hasattr(oauth, "google"):
        raise HTTPException(status_code=501, detail="Google OAuth not configured.")
    token_data = await oauth.google.authorize_access_token(request)
    info = token_data.get("userinfo") or {}
    return _oauth_upsert_redirect(session, info.get("email", ""), info.get("name", ""))


# ── Auth: GitHub OAuth ────────────────────────────────────────────────────────

@app.get("/auth/github")
async def github_login(request: Request):
    if not hasattr(oauth, "github"):
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured.")
    redirect_uri = str(request.url_for("github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/github/callback", name="github_callback")
async def github_callback(request: Request, session: Session = Depends(get_session)):
    if not hasattr(oauth, "github"):
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured.")
    token_data = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token_data)
    info = resp.json() if resp else {}
    email = info.get("email") or f"gh_{info.get('id', 'unknown')}@github.invalid"
    return _oauth_upsert_redirect(session, email, info.get("login", ""))


# ── Auth: Dropbox OAuth ───────────────────────────────────────────────────────

@app.get("/auth/dropbox")
async def dropbox_login(request: Request):
    if not hasattr(oauth, "dropbox"):
        raise HTTPException(status_code=501, detail="Dropbox OAuth not configured.")
    redirect_uri = str(request.url_for("dropbox_callback"))
    return await oauth.dropbox.authorize_redirect(request, redirect_uri)


@app.get("/auth/dropbox/callback", name="dropbox_callback")
async def dropbox_callback(request: Request, session: Session = Depends(get_session)):
    if not hasattr(oauth, "dropbox"):
        raise HTTPException(status_code=501, detail="Dropbox OAuth not configured.")
    token_data = await oauth.dropbox.authorize_access_token(request)
    access_token = token_data.get("access_token", "")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.dropboxapi.com/2/users/get_current_account",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            content=b"null",
        )
        info = r.json() if r.status_code == 200 else {}
    email = info.get("email", "")
    name = info.get("name", {}).get("display_name", "") if isinstance(info.get("name"), dict) else ""
    return _oauth_upsert_redirect(session, email, name)


# ── OAuth shared helper ───────────────────────────────────────────────────────

def _oauth_upsert_redirect(session: Session, email: str, display_name: str) -> RedirectResponse:
    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=oauth_no_email")
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        # Block if the existing account was registered with a password (not OAuth)
        if not verify_password(f"oauth_{email}", user.hashed_password):
            return RedirectResponse(f"{FRONTEND_URL}/login?error=email_password_account")
        # Existing OAuth account — log in
    else:
        # New user — create an OAuth account
        base = (display_name or email.split("@")[0])[:50].replace(" ", "_") or "user"
        username = base
        suffix = 1
        while session.exec(select(User).where(User.username == username)).first():
            username = f"{base}{suffix}"
            suffix += 1
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(f"oauth_{email}"),  # unusable placeholder
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    token = create_access_token(user.id)
    return RedirectResponse(f"{FRONTEND_URL}/oauth-callback?token={token}")


# ── Analysis ──────────────────────────────────────────────────────────────────

@app.post("/api/analyze", response_model=AnalysisResponse, status_code=201)
@limiter.limit("20/minute")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if not is_valid_image_bytes(payload):
        raise HTTPException(status_code=400, detail="File content is not a recognised image format.")
    try:
        result = analysis_service.analyze(payload, file.filename or "upload.png")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    JobService.create_job(session, {
        "job_id": result.job_id,
        "user_id": current_user.id,
        "status": result.status,
        "cell_count": result.cell_count,
        "mode": result.metadata["mode"],
        "original_filename": result.metadata["original_filename"],
        "input_url": result.input_url,
        "mask_url": result.mask_url,
        "overlay_url": result.overlay_url,
        "processing_ms": result.metadata["processing_ms"],
        "threshold": result.metadata.get("threshold"),
        "min_area": result.metadata["min_area"],
        "image_size": result.metadata["image_size"],
        "device": result.metadata["device"],
    })
    return AnalysisResponse(**analysis_service.result_to_dict(result))


# ── Jobs ──────────────────────────────────────────────────────────────────────

@app.get("/api/jobs", response_model=List[JobSummary])
def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=500),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[JobSummary]:
    if current_user.role in _ELEVATED:
        jobs = JobService.list_jobs(session, skip=skip, limit=limit)
    else:
        jobs = JobService.list_jobs_by_user(session, current_user.id, skip=skip, limit=limit)
    return [
        JobSummary(
            id=j.id,
            job_id=j.job_id,
            status=j.status,
            cell_count=j.cell_count,
            mode=j.mode,
            original_filename=j.original_filename,
            created_at=j.created_at,
            annotation_count=len(j.annotations) if j.annotations else 0,
        )
        for j in jobs
    ]


# NOTE: this route must stay above /{job_id} so "export.csv" is not captured as a job_id
@app.get("/api/jobs/export.csv", include_in_schema=True)
def export_jobs_csv(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download all accessible jobs as a CSV file."""
    if current_user.role in _ELEVATED:
        jobs = JobService.list_jobs(session, skip=0, limit=10_000)
    else:
        jobs = JobService.list_jobs_by_user(session, current_user.id, skip=0, limit=10_000)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "job_id", "original_filename", "cell_count", "mode",
        "device", "processing_ms", "threshold", "min_area",
        "image_size", "status", "created_at",
    ])
    for j in jobs:
        writer.writerow([
            j.job_id, j.original_filename, j.cell_count, j.mode,
            j.device, j.processing_ms, j.threshold, j.min_area,
            j.image_size, j.status,
            j.created_at.isoformat(),
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nuclei-jobs.csv"},
    )


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    job = JobService.get_job_by_job_id(session, job_id)
    if current_user.role not in _ELEVATED and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your job.")
    return job


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    job = JobService.get_job_by_job_id(session, job_id)
    if current_user.role not in _ELEVATED and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your job.")
    JobService.delete_job(session, job_id)


# ── Annotations ───────────────────────────────────────────────────────────────

@app.post("/api/jobs/{job_id}/annotations", response_model=AnnotationResponse, status_code=201)
def create_annotation(
    job_id: str,
    data: AnnotationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnnotationResponse:
    return AnnotationService.create_annotation(session, job_id, data, user_id=current_user.id)


@app.get("/api/jobs/{job_id}/annotations", response_model=List[AnnotationResponse])
def list_annotations(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[AnnotationResponse]:
    return AnnotationService.list_annotations(session, job_id)


@app.delete("/api/annotations/{annotation_id}", status_code=204)
def delete_annotation(
    annotation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    AnnotationService.delete_annotation(session, annotation_id)


# ── File serving ──────────────────────────────────────────────────────────────

@app.get("/files/{filename}")
def get_file(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    target = (RESULT_DIR / filename).resolve()
    if not str(target).startswith(str(RESULT_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(target)


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.get("/admin/users", response_model=List[UserResponse])
def admin_list_users(
    session: Session = Depends(get_session),
    current: User = Depends(require_role(*_ELEVATED)),
) -> List[UserResponse]:
    """Manager sees everyone. Admin sees non-managers only."""
    users = session.exec(select(User)).all()
    if current.role == UserRole.admin:
        users = [u for u in users if u.role != UserRole.manager]
    return [UserResponse.model_validate(u) for u in users]


@app.post("/admin/users", response_model=UserResponse, status_code=201)
def admin_create_admin(
    data: CreateAdminRequest,
    session: Session = Depends(get_session),
    _manager: User = Depends(require_role(UserRole.manager)),
) -> UserResponse:
    """Manager-only: create a new admin account."""
    clash = session.exec(
        select(User).where((User.email == data.email) | (User.username == data.username))
    ).first()
    if clash:
        raise HTTPException(status_code=409, detail="Username or email already registered.")
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.admin,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse.model_validate(user)


@app.patch("/admin/users/{user_id}/role", response_model=UserResponse)
def admin_update_role(
    user_id: int,
    data: RoleUpdateRequest,
    session: Session = Depends(get_session),
    current: User = Depends(require_role(*_ELEVATED)),
) -> UserResponse:
    """Change a user's role — only viewer↔researcher swaps are allowed here."""
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role.")
    # Managers cannot be touched by anyone
    if target.role == UserRole.manager:
        raise HTTPException(status_code=403, detail="Cannot modify a manager.")
    # Admins cannot touch other admins
    if current.role == UserRole.admin and target.role == UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin cannot modify another admin.")
    # Only manager can promote to admin
    if data.role == "admin" and current.role != UserRole.manager:
        raise HTTPException(status_code=403, detail="Only a manager can assign the admin role.")
    target.role = UserRole(data.role)
    session.add(target)
    session.commit()
    session.refresh(target)
    return UserResponse.model_validate(target)


@app.delete("/admin/users/{user_id}", status_code=204)
def admin_delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current: User = Depends(require_role(*_ELEVATED)),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself.")
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    # Nobody can delete a manager
    if target.role == UserRole.manager:
        raise HTTPException(status_code=403, detail="Cannot delete a manager.")
    # Admin can only delete viewers/researchers
    if current.role == UserRole.admin and target.role not in _MANAGEABLE:
        raise HTTPException(status_code=403, detail="Admin cannot delete another admin.")
    session.delete(target)
    session.commit()


@app.get("/admin/stats")
def admin_stats(
    session: Session = Depends(get_session),
    _elevated: User = Depends(require_role(*_ELEVATED)),
) -> dict:
    users = list(session.exec(select(User)).all())
    jobs = list(session.exec(select(AnalysisJob)).all())
    by_role = {role.value: 0 for role in UserRole}
    for u in users:
        by_role[u.role.value] += 1
    return {
        "total_users": len(users),
        "users_by_role": by_role,
        "total_jobs": len(jobs),
        "total_cells": sum(j.cell_count for j in jobs),
    }


# ── Reset DB (dev only — route not registered in production) ─────────────────

if ENV != "production":
    @app.post("/reset-db", include_in_schema=False)
    def reset_db(session: Session = Depends(get_session)) -> dict:
        with engine.connect() as conn:
            for table in reversed(SQLModel.metadata.sorted_tables):
                conn.execute(text(f"DELETE FROM {table.name}"))
            conn.commit()
        return {"status": "reset"}
