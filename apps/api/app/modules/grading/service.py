from uuid import UUID

from celery import Celery
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.jobs.errors import job_enqueue_failed, job_update_failed
from app.modules.jobs.models import JobLog
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.status import AI_GRADING_QUEUE, DETERMINISTIC_GRADING_QUEUE, JobStatus, JobType


DETERMINISTIC_GRADING_TASK_NAME = "apps.worker.tasks.deterministic_grading_tasks.grade_submission"
AI_GRADING_TASK_NAME = "apps.worker.tasks.ai_grading_tasks.grade_subjective_submission"


class GradingDispatchService:
    def __init__(self, db: Session) -> None:
        self.repository = JobRepository(db)
        self.celery_app = Celery(
            "class_centric_exam_api",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )

    def enqueue_deterministic_grading(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        submission_id: UUID,
    ) -> JobLog:
        payload = {
            "teacher_id": str(teacher_id),
            "class_id": str(class_id),
            "exam_id": str(exam_id),
            "submission_id": str(submission_id),
        }
        job = JobLog(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            submission_id=submission_id,
            job_type=JobType.DETERMINISTIC_GRADING.value,
            queue_name=DETERMINISTIC_GRADING_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="submission",
            entity_id=submission_id,
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
                DETERMINISTIC_GRADING_TASK_NAME,
                args=[task_payload],
                queue=DETERMINISTIC_GRADING_QUEUE,
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

    def enqueue_ai_grading(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        submission_id: UUID,
    ) -> JobLog:
        payload = {
            "teacher_id": str(teacher_id),
            "class_id": str(class_id),
            "exam_id": str(exam_id),
            "submission_id": str(submission_id),
        }
        job = JobLog(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            submission_id=submission_id,
            job_type=JobType.AI_GRADING.value,
            queue_name=AI_GRADING_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="submission",
            entity_id=submission_id,
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
                AI_GRADING_TASK_NAME,
                args=[task_payload],
                queue=AI_GRADING_QUEUE,
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
