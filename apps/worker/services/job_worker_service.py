from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from apps.worker.shared.worker_context import worker_db_session
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import JobStatus


class JobWorkerService:
    def run_test_ping(self, job_id: str, payload: dict) -> dict:
        job_uuid = UUID(job_id)
        result = {"message": "pong"}

        with worker_db_session() as db:
            job = db.scalar(select(JobLog).where(JobLog.id == job_uuid))
            if job is None:
                raise ValueError(f"Job log not found: {job_id}")

            try:
                job.status = JobStatus.RUNNING.value
                job.started_at = datetime.now(timezone.utc)
                job.attempts = (job.attempts or 0) + 1
                db.add(job)
                db.commit()

                job.result_json = result
                job.status = JobStatus.SUCCESS.value
                job.finished_at = datetime.now(timezone.utc)
                db.add(job)
                db.commit()
                return result
            except Exception as exc:
                db.rollback()
                job.status = JobStatus.FAILED.value
                job.error_message = str(exc)
                job.finished_at = datetime.now(timezone.utc)
                db.add(job)
                db.commit()
                raise

