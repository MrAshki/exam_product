from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.jobs.errors import job_access_denied, job_not_found
from app.modules.jobs.models import JobLog
from app.modules.jobs.repository import JobRepository


class JobService:
    def __init__(self, db: Session) -> None:
        self.repository = JobRepository(db)

    def get_for_teacher(self, job_id: UUID, teacher: User) -> JobLog:
        job = self.repository.get(job_id)
        if job is None:
            raise job_not_found()
        if job.teacher_id != teacher.id:
            raise job_access_denied()
        return job
