"""Pydantic request/response DTOs — separate from ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from backend.auth_utils import validate_password_strength
from backend.models import UserRole


# ── Health / Analysis ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool
    mode: Literal["model", "fallback-demo", "uninitialised"]
    load_error: Optional[str] = None


class AnalysisMetadata(BaseModel):
    original_filename: str
    mode: Literal["model", "fallback-demo"]
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    min_area: int = Field(ge=1)
    image_size: int = Field(ge=1)
    processing_ms: int = Field(ge=0)
    device: str


class AnalysisResponse(BaseModel):
    job_id: str
    status: Literal["ok", "ok-fallback"]
    message: str
    cell_count: int = Field(ge=0)
    input_url: str
    mask_url: str
    overlay_url: str
    metadata: AnalysisMetadata


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TwoFactorRequiredResponse(BaseModel):
    requires_2fa: bool = True
    temp_token: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    uri: str


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class EmailOTPRequest(BaseModel):
    email: EmailStr


class EmailOTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class VerifyResetCodeResponse(BaseModel):
    reset_token: str
    message: str = "Code verified. You can now reset your password."


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


# ── Annotation ────────────────────────────────────────────────────────────────

class AnnotationCreate(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    user_id: int
    note: str
    created_at: datetime


# ── Job ───────────────────────────────────────────────────────────────────────

class JobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    status: str
    cell_count: int
    mode: str
    original_filename: str
    created_at: datetime
    annotation_count: int = 0
    publication_id: Optional[int] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    user_id: Optional[int]
    status: str
    cell_count: int
    mode: str
    original_filename: str
    input_url: str
    mask_url: str
    overlay_url: str
    processing_ms: int
    threshold: Optional[float]
    min_area: int
    image_size: int
    device: str
    created_at: datetime
    annotations: List[AnnotationResponse] = []


# ── Publication & Explore ─────────────────────────────────────────────────────

class PublishRequest(BaseModel):
    headline: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=2000)


class PublicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    job_uid: str
    user_id: int
    username: str
    headline: str
    description: str
    cell_count: int
    mode: str
    overlay_url: str
    mask_url: str
    input_url: str
    original_filename: str
    created_at: datetime
    is_favourited: bool = False
    comment_count: int = 0


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: int
    publication_id: int
    user_id: int
    username: str
    text: str
    created_at: datetime


class NotificationResponse(BaseModel):
    id: int
    actor_username: str
    kind: str
    publication_id: int
    publication_headline: str
    read: bool
    created_at: datetime


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    totp_enabled: bool = False
    created_at: datetime


class RoleUpdateRequest(BaseModel):
    """Manager can set viewer/researcher/admin. Admin can only set viewer/researcher."""
    role: Literal["viewer", "researcher", "admin"]


class SelfRoleRequest(BaseModel):
    """Viewer/researcher can switch their own role between these two."""
    role: Literal["viewer", "researcher"]


class CreateAdminRequest(BaseModel):
    """Manager-only: create a new user with role=admin."""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)
