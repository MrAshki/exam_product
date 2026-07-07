from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.jobs.models import JobLog


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, job: JobLog) -> JobLog:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, job_id: UUID) -> JobLog | None:
        return self.db.scalar(select(JobLog).where(JobLog.id == job_id))

    def save(self, job: JobLog) -> JobLog:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def rollback(self) -> None:
        self.db.rollback()

