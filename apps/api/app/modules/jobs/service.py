from typing import Any
from uuid import UUID

from celery import Celery
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.jobs.errors import job_access_denied, job_enqueue_failed, job_not_found, job_update_failed
from app.modules.jobs.models import JobLog
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.status import DEFAULT_QUEUE, JobStatus, JobType


TEST_PING_TASK_NAME = "apps.worker.tasks.test_tasks.test_ping"


class JobService:
    def __init__(self, db: Session) -> None:
        self.repository = JobRepository(db)
        self.celery_app = Celery(
            "class_centric_exam_api",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )

    def get_for_teacher(self, job_id: UUID, teacher: User) -> JobLog:
        job = self.repository.get(job_id)
        if job is None:
            raise job_not_found()
        if job.teacher_id != teacher.id:
            raise job_access_denied()
        return job

    def enqueue_test_ping(self, teacher: User, payload: dict[str, Any] | None = None) -> JobLog:
        job = JobLog(
            teacher_id=teacher.id,
            job_type=JobType.TEST_PING.value,
            queue_name=DEFAULT_QUEUE,
            status=JobStatus.QUEUED.value,
            payload_json=payload,
        )

        try:
            job = self.repository.create(job)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise job_update_failed() from exc

        try:
            task_result = self.celery_app.send_task(
                TEST_PING_TASK_NAME,
                args=[str(job.id), payload or {}],
                queue=DEFAULT_QUEUE,
            )
        except Exception as exc:
            job.status = JobStatus.FAILED.value
            job.error_code = "JOB_ENQUEUE_FAILED"
            job.error_message = str(exc)
            try:
                self.repository.save(job)
            except SQLAlchemyError:
                self.repository.rollback()
            raise job_enqueue_failed() from exc

        job.celery_task_id = task_result.id
        try:
            return self.repository.save(job)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise job_update_failed() from exc

