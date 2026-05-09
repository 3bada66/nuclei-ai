"""SQLModel ORM table definitions — one class per database table."""

import enum
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, enum.Enum):
    manager = "manager"   # highest — created only via seed/script
    admin = "admin"
    researcher = "researcher"
    viewer = "viewer"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.viewer)
    totp_secret: Optional[str] = Field(default=None, max_length=64)
    totp_enabled: bool = Field(default=False)
    email_otp_hash: Optional[str] = Field(default=None, max_length=255)
    email_otp_expires_at: Optional[datetime] = Field(default=None)
    reset_token_hash: Optional[str] = Field(default=None, max_length=255)
    reset_token_expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    jobs: List["AnalysisJob"] = Relationship(back_populates="user")
    annotations: List["Annotation"] = Relationship(back_populates="user")


class AnalysisJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True, max_length=12)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    status: str = Field(max_length=20)
    cell_count: int = Field(ge=0)
    mode: str = Field(max_length=20)
    original_filename: str = Field(max_length=255)
    input_url: str = Field(max_length=255)
    mask_url: str = Field(max_length=255)
    overlay_url: str = Field(max_length=255)
    processing_ms: int = Field(ge=0)
    threshold: Optional[float] = Field(default=None)
    min_area: int = Field(default=1, ge=1)
    image_size: int = Field(default=256, ge=1)
    device: str = Field(default="cpu", max_length=10)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional[User] = Relationship(back_populates="jobs")
    annotations: List["Annotation"] = Relationship(back_populates="job")


class Annotation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="analysisjob.id")
    user_id: int = Field(foreign_key="user.id")
    note: str = Field(max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    job: Optional[AnalysisJob] = Relationship(back_populates="annotations")
    user: Optional[User] = Relationship(back_populates="annotations")
