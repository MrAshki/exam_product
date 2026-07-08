from typing import Any
from uuid import UUID

from celery import Celery
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.jobs.errors import job_enqueue_failed, job_update_failed
from app.modules.jobs.models import JobLog
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.status import EMAIL_QUEUE, JobStatus, JobType


EMAIL_SEND_TASK_NAME = "apps.worker.tasks.email_tasks.send_email"


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.repository = JobRepository(db)
        self.celery_app = Celery(
            "class_centric_exam_api",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )

    def enqueue_email(
        self,
        *,
        email_type: str,
        to_email: str,
        template_payload: dict[str, Any],
        teacher_id: UUID | None = None,
        class_id: UUID | None = None,
        exam_id: UUID | None = None,
        student_id: UUID | None = None,
    ) -> JobLog:
        payload = {
            "email_type": email_type,
            "teacher_id": str(teacher_id) if teacher_id else None,
            "class_id": str(class_id) if class_id else None,
            "exam_id": str(exam_id) if exam_id else None,
            "student_id": str(student_id) if student_id else None,
            "to_email": to_email,
            "template_payload": template_payload,
        }
        job = JobLog(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            job_type=JobType.EMAIL_SEND.value,
            queue_name=EMAIL_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type=email_type,
            entity_id=exam_id,
            payload_json=payload,
        )

        try:
            job = self.repository.create(job)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise job_update_failed() from exc

        task_payload = {"job_id": str(job.id), **payload}
        try:
            task_result = self.celery_app.send_task(
                EMAIL_SEND_TASK_NAME,
                args=[task_payload],
                queue=EMAIL_QUEUE,
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
