"""Database CRUD operations — all business logic lives here, routes stay thin."""

from __future__ import annotations

from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select

from backend.models import AnalysisJob, Annotation, User
from backend.schemas import AnnotationCreate


# ── Job CRUD ──────────────────────────────────────────────────────────────────

class JobService:

    @staticmethod
    def create_job(session: Session, data: dict) -> AnalysisJob:
        job = AnalysisJob(**data)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    @staticmethod
    def get_job_by_job_id(session: Session, job_id: str) -> AnalysisJob:
        job = session.exec(
            select(AnalysisJob).where(AnalysisJob.job_id == job_id)
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return job

    @staticmethod
    def list_jobs(session: Session, skip: int = 0, limit: int = 20) -> List[AnalysisJob]:
        return list(
            session.exec(
                select(AnalysisJob)
                .order_by(AnalysisJob.created_at.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        )

    @staticmethod
    def list_jobs_by_user(
        session: Session, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[AnalysisJob]:
        return list(
            session.exec(
                select(AnalysisJob)
                .where(AnalysisJob.user_id == user_id)
                .order_by(AnalysisJob.created_at.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        )

    @staticmethod
    def delete_job(session: Session, job_id: str) -> None:
        job = JobService.get_job_by_job_id(session, job_id)
        session.delete(job)
        session.commit()


# ── Annotation CRUD ───────────────────────────────────────────────────────────

class AnnotationService:

    @staticmethod
    def create_annotation(
        session: Session,
        job_id_str: str,
        data: AnnotationCreate,
        user_id: int,
    ) -> Annotation:
        job = JobService.get_job_by_job_id(session, job_id_str)
        annotation = Annotation(job_id=job.id, user_id=user_id, note=data.note)
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
        return annotation

    @staticmethod
    def list_annotations(session: Session, job_id_str: str) -> List[Annotation]:
        job = JobService.get_job_by_job_id(session, job_id_str)
        return list(
            session.exec(
                select(Annotation).where(Annotation.job_id == job.id)
            ).all()
        )

    @staticmethod
    def delete_annotation(session: Session, annotation_id: int) -> None:
        annotation = session.get(Annotation, annotation_id)
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found.")
        session.delete(annotation)
        session.commit()


# ── User CRUD (stubs — expanded in Phase 2) ───────────────────────────────────

class UserService:

    @staticmethod
    def get_by_id(session: Session, user_id: int) -> User:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        return user

    @staticmethod
    def list_users(session: Session) -> List[User]:
        return list(session.exec(select(User)).all())
