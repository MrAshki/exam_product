from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from apps.worker.shared.worker_context import worker_db_session
from app.infrastructure.email.email_logger import EmailLogger
from app.infrastructure.email.email_service import EmailService
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import JobStatus
from app.modules.notifications.constants import EmailStatus


class JobWorkerService:
    def run_email_send(self, payload: dict) -> dict:
        job_id = payload["job_id"]
        job_uuid = UUID(job_id)

        with worker_db_session() as db:
            job = db.scalar(select(JobLog).where(JobLog.id == job_uuid))
            if job is None:
                raise ValueError(f"Job log not found: {job_id}")

            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.now(timezone.utc)
            job.attempts = (job.attempts or 0) + 1
            db.add(job)
            db.commit()

            try:
                result = EmailService(db).send_email(
                    email_type=payload["email_type"],
                    to_email=payload["to_email"],
                    template_payload=payload.get("template_payload") or {},
                    teacher_id=self._optional_uuid(payload.get("teacher_id")),
                    class_id=self._optional_uuid(payload.get("class_id")),
                    exam_id=self._optional_uuid(payload.get("exam_id")),
                    student_id=self._optional_uuid(payload.get("student_id")),
                )
            except Exception as exc:
                db.rollback()
                self._safe_log_failed_email(db, payload, str(exc))
                job.status = JobStatus.FAILED.value
                job.error_message = str(exc)
                job.finished_at = datetime.now(timezone.utc)
                db.add(job)
                db.commit()
                return {"success": False, "error_message": str(exc)}

            response = {
                "success": result.success,
                "provider_message_id": result.provider_message_id,
                "error_message": result.error_message,
                "raw_response": result.raw_response,
            }
            job.result_json = response
            job.status = JobStatus.SUCCESS.value if result.success else JobStatus.FAILED.value
            job.error_message = result.error_message
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return response

    @staticmethod
    def _optional_uuid(value: str | None) -> UUID | None:
        return UUID(value) if value else None

    def _safe_log_failed_email(self, db, payload: dict, error_message: str) -> None:
        if not payload.get("to_email") or not payload.get("email_type"):
            return
        try:
            EmailLogger(db).log_attempt(
                email=payload["to_email"],
                email_type=payload["email_type"],
                status=EmailStatus.FAILED,
                teacher_id=self._optional_uuid(payload.get("teacher_id")),
                class_id=self._optional_uuid(payload.get("class_id")),
                exam_id=self._optional_uuid(payload.get("exam_id")),
                student_id=self._optional_uuid(payload.get("student_id")),
                error_message=error_message,
            )
        except Exception:
            db.rollback()
