from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from apps.worker.shared.worker_context import worker_db_session
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import ExamStatus
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import JobStatus
from app.modules.results.models import LeaderboardToken


class LeaderboardWorkerService:
    def run(self, payload: dict) -> dict:
        job_id = payload["job_id"]
        job_uuid = UUID(job_id)

        with worker_db_session() as db:
            job = db.scalar(select(JobLog).where(JobLog.id == job_uuid))
            if job is None:
                return {"success": False, "error_message": f"Job log not found: {job_id}"}

            self._mark_running(db, job)
            try:
                result = self._validate_leaderboard(db, payload)
            except Exception as exc:
                db.rollback()
                self._mark_failed(db, job, str(exc))
                return {"success": False, "error_message": str(exc)}

            job.result_json = result
            job.status = JobStatus.SUCCESS.value
            job.error_code = None
            job.error_message = None
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return result

    def _validate_leaderboard(self, db, payload: dict) -> dict:
        teacher_id = self._required_uuid(payload, "teacher_id")
        class_id = self._required_uuid(payload, "class_id")
        exam_id = self._required_uuid(payload, "exam_id")

        classroom = db.scalar(
            select(Classroom).where(
                Classroom.id == class_id,
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
        )
        if classroom is None:
            raise ValueError("Class not found or mismatched.")

        exam = db.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.teacher_id == teacher_id,
                Exam.class_id == class_id,
                Exam.deleted_at.is_(None),
            )
        )
        if exam is None:
            raise ValueError("Exam not found or mismatched.")
        if exam.status != ExamStatus.PUBLISHED.value:
            raise ValueError("Exam is not published.")
        if not exam.show_leaderboard:
            raise ValueError("Leaderboard is disabled for this exam.")

        token = db.scalar(
            select(LeaderboardToken).where(
                LeaderboardToken.class_id == class_id,
                LeaderboardToken.exam_id == exam_id,
                LeaderboardToken.deleted_at.is_(None),
            )
        )
        if token is None:
            raise ValueError("Leaderboard token not found.")

        return {
            "success": True,
            "class_id": str(class_id),
            "exam_id": str(exam_id),
            "leaderboard_token_id": str(token.id),
        }

    @staticmethod
    def _required_uuid(payload: dict, key: str) -> UUID:
        value = payload.get(key)
        if not value:
            raise ValueError(f"Missing payload field: {key}")
        return UUID(str(value))

    @staticmethod
    def _mark_running(db, job: JobLog) -> None:
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        job.finished_at = None
        job.attempts = (job.attempts or 0) + 1
        db.add(job)
        db.commit()

    @staticmethod
    def _mark_failed(db, job: JobLog, error_message: str) -> None:
        job.status = JobStatus.FAILED.value
        job.error_message = error_message
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
