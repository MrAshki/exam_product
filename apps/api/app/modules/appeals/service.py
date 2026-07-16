from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from celery import Celery
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.appeals import errors
from app.modules.appeals.models import Appeal
from app.modules.appeals.repository import AppealRepository
from app.modules.appeals.schemas import AppealCreate, AppealResolveRequest
from app.modules.appeals.status import AppealStatus
from app.modules.auth.models import User
from app.modules.exams.status import ExamStatus
from app.modules.grading.feedback import safe_ai_feedback
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE, LEADERBOARD_QUEUE, JobStatus, JobType
from app.modules.notifications.constants import EmailType
from app.modules.submissions.models import Answer, Submission


EMAIL_SEND_TASK_NAME = "apps.worker.tasks.email_tasks.send_email"
LEADERBOARD_UPDATE_TASK_NAME = "apps.worker.tasks.leaderboard_tasks.update_leaderboard"


class AppealService:
    def __init__(self, db: Session) -> None:
        self.repository = AppealRepository(db)
        self.celery_app = Celery(
            "class_centric_exam_api",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )

    def submit_appeal(self, result_token: str, payload: AppealCreate) -> dict:
        context = self.repository.get_result_context(result_token)
        if context is None:
            raise errors.invalid_result_token()
        token, exam, classroom, student, submission, teacher = context
        if exam.status != ExamStatus.PUBLISHED.value or submission.published_at is None:
            raise errors.result_not_published()
        if not exam.allow_appeals:
            raise errors.appeals_not_allowed()

        answer_id = payload.answer_id
        if answer_id is not None and self.repository.get_answer_for_submission(submission, answer_id) is None:
            raise errors.answer_not_in_submission()
        if self.repository.pending_appeal_exists(submission.id, answer_id):
            raise errors.appeal_already_exists()

        appeal = Appeal(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            student_id=student.id,
            submission_id=submission.id,
            answer_id=answer_id,
            message=payload.message,
            status=AppealStatus.PENDING.value,
        )
        try:
            self.repository.create_appeal(appeal)
            self.repository.save(appeal)
            self.repository.refresh(appeal)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise errors.validation_error({"database": [str(exc)]}) from exc

        self._enqueue_appeal_created_email(
            appeal=appeal,
            teacher=teacher,
            student_full_name=student.full_name,
            classroom_title=classroom.title,
            exam_title=exam.title,
        )
        return {"appeal_id": str(appeal.id), "status": appeal.status}

    def list_appeals(
        self,
        *,
        class_id: UUID,
        teacher: User,
        status: str | None,
        exam_id: UUID | None,
        student_id: UUID | None,
        page: int,
        page_size: int,
    ) -> dict:
        self._ensure_class(class_id, teacher.id)
        if status is not None and status not in {item.value for item in AppealStatus}:
            raise errors.invalid_appeal_status({"status": ["Invalid appeal status."]})
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        rows, total = self.repository.list_appeals(
            class_id=class_id,
            teacher_id=teacher.id,
            status=status,
            exam_id=exam_id,
            student_id=student_id,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [
                {
                    "id": str(appeal.id),
                    "student_id": str(student.id),
                    "student_full_name": student.full_name,
                    "exam_id": str(exam.id),
                    "exam_title": exam.title,
                    "answer_id": str(appeal.answer_id) if appeal.answer_id else None,
                    "status": appeal.status,
                    "created_at": appeal.created_at,
                }
                for appeal, student, exam in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def get_appeal(self, *, class_id: UUID, appeal_id: UUID, teacher: User) -> dict:
        self._ensure_class(class_id, teacher.id)
        context = self.repository.get_appeal_context(class_id=class_id, appeal_id=appeal_id, teacher_id=teacher.id)
        if context is None:
            raise errors.appeal_not_found()
        appeal, student, exam, _classroom, submission, _result_token, answer, question = context
        return self._detail_payload(appeal, student, exam, submission, answer, question)

    def resolve_appeal(
        self,
        *,
        class_id: UUID,
        appeal_id: UUID,
        payload: AppealResolveRequest,
        teacher: User,
    ) -> dict:
        self._ensure_class(class_id, teacher.id)
        context = self.repository.get_appeal_context(class_id=class_id, appeal_id=appeal_id, teacher_id=teacher.id)
        if context is None:
            raise errors.appeal_not_found()
        appeal, student, exam, classroom, submission, result_token, answer, question = context
        if appeal.status != AppealStatus.PENDING.value:
            raise errors.appeal_already_resolved()

        score_changed = False
        final_decision = payload.status
        old_score = None
        new_score = None
        if final_decision == AppealStatus.ACCEPTED.value and payload.new_score is not None:
            if appeal.answer_id is None or answer is None or question is None:
                raise errors.answer_not_found()
            self._validate_score(payload.new_score, answer, question)
            old_score = answer.final_score
            new_score = payload.new_score
            answer.teacher_score = payload.new_score
            answer.final_score = payload.new_score
            answer.reviewed_by_teacher = True
            answer.needs_review = False
            appeal.old_score = old_score
            appeal.new_score = new_score
            score_changed = old_score != new_score
            if score_changed:
                self.repository.create_grade_change_log(
                    answer=answer,
                    old_score=old_score,
                    new_score=new_score,
                    reason=f"Appeal resolved ({final_decision}): {payload.teacher_response}",
                )
                self._recalculate_submission(submission)

        now = datetime.now(timezone.utc)
        appeal.status = AppealStatus.RESOLVED.value
        appeal.teacher_response = payload.teacher_response
        appeal.resolved_at = now

        try:
            objects = [appeal, submission]
            if answer is not None:
                objects.append(answer)
            self.repository.save(*objects)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise errors.validation_error({"database": [str(exc)]}) from exc

        self._enqueue_appeal_resolved_email(
            appeal=appeal,
            student_email=student.email,
            student_full_name=student.full_name,
            class_title=classroom.title,
            exam_title=exam.title,
            final_decision=final_decision,
            teacher_response=payload.teacher_response,
            score_changed=score_changed,
            result_token=result_token.token if result_token is not None else None,
        )
        if score_changed and exam.status == ExamStatus.PUBLISHED.value and exam.show_leaderboard:
            self._enqueue_leaderboard_update(appeal.teacher_id, appeal.class_id, appeal.exam_id)

        return {
            "appeal_id": str(appeal.id),
            "status": appeal.status,
            "final_decision": final_decision,
            "score_changed": score_changed,
        }

    def _ensure_class(self, class_id: UUID, teacher_id: UUID) -> None:
        if self.repository.get_class_for_teacher(class_id, teacher_id) is None:
            raise errors.class_not_found()

    def _recalculate_submission(self, submission: Submission) -> None:
        questions = self.repository.list_confirmed_questions(submission)
        answers = self.repository.list_active_answers_for_submission(submission)
        submission.max_score = sum((Decimal(question.points) for question in questions), Decimal("0"))
        submission.total_score = sum(
            (answer.final_score for answer in answers if answer.final_score is not None),
            Decimal("0"),
        )
        submission.needs_review_count = sum(1 for answer in answers if answer.needs_review)

    @staticmethod
    def _validate_score(score: Decimal, answer: Answer, question) -> None:
        max_score = answer.max_score if answer.max_score is not None else Decimal(question.points)
        if score < 0 or score > max_score:
            raise errors.invalid_score({"new_score": [f"Score must be between 0 and {max_score}."]})

    def _enqueue_appeal_created_email(
        self,
        *,
        appeal: Appeal,
        teacher: User,
        student_full_name: str,
        classroom_title: str,
        exam_title: str,
    ) -> None:
        payload = {
            "email_type": EmailType.APPEAL_CREATED.value,
            "teacher_id": str(appeal.teacher_id),
            "class_id": str(appeal.class_id),
            "exam_id": str(appeal.exam_id),
            "student_id": str(appeal.student_id),
            "to_email": teacher.email,
            "template_payload": {
                "teacher_full_name": teacher.full_name,
                "student_full_name": student_full_name,
                "class_title": classroom_title,
                "exam_title": exam_title,
                "appeal_message": appeal.message,
                "appeal_link": f"{settings.FRONTEND_BASE_URL}/dashboard/classes/{appeal.class_id}/appeals/{appeal.id}",
            },
        }
        self._enqueue_email_job(appeal, payload)

    def _enqueue_appeal_resolved_email(
        self,
        *,
        appeal: Appeal,
        student_email: str,
        student_full_name: str,
        class_title: str,
        exam_title: str,
        final_decision: str,
        teacher_response: str,
        score_changed: bool,
        result_token: str | None,
    ) -> None:
        payload = {
            "email_type": EmailType.APPEAL_RESOLVED.value,
            "teacher_id": str(appeal.teacher_id),
            "class_id": str(appeal.class_id),
            "exam_id": str(appeal.exam_id),
            "student_id": str(appeal.student_id),
            "to_email": student_email,
            "template_payload": {
                "student_full_name": student_full_name,
                "class_title": class_title,
                "exam_title": exam_title,
                "final_decision": final_decision,
                "appeal_status": AppealStatus.RESOLVED.value,
                "teacher_response": teacher_response,
                "score_changed": score_changed,
                "result_link": f"{settings.FRONTEND_BASE_URL}/result/{result_token}" if result_token else None,
            },
        }
        self._enqueue_email_job(appeal, payload)

    def _enqueue_email_job(self, appeal: Appeal, payload: dict) -> None:
        job = JobLog(
            teacher_id=appeal.teacher_id,
            class_id=appeal.class_id,
            exam_id=appeal.exam_id,
            job_type=JobType.EMAIL_SEND.value,
            queue_name=EMAIL_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="appeal",
            entity_id=appeal.id,
            payload_json=payload,
        )
        self._create_and_enqueue(job, payload, EMAIL_SEND_TASK_NAME, EMAIL_QUEUE)

    def _enqueue_leaderboard_update(self, teacher_id: UUID, class_id: UUID, exam_id: UUID) -> None:
        payload = {
            "teacher_id": str(teacher_id),
            "class_id": str(class_id),
            "exam_id": str(exam_id),
        }
        job = JobLog(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            job_type=JobType.LEADERBOARD_UPDATE.value,
            queue_name=LEADERBOARD_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="exam",
            entity_id=exam_id,
            payload_json=payload,
        )
        self._create_and_enqueue(job, payload, LEADERBOARD_UPDATE_TASK_NAME, LEADERBOARD_QUEUE)

    def _create_and_enqueue(self, job: JobLog, payload: dict, task_name: str, queue_name: str) -> JobLog:
        try:
            self.repository.create_job_log(job)
            self.repository.save(job)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise errors.job_enqueue_failed({"database": [str(exc)]}) from exc

        task_payload = {"job_id": str(job.id), **payload}
        try:
            task_result = self.celery_app.send_task(task_name, args=[task_payload], queue=queue_name)
        except Exception as exc:
            job.status = JobStatus.FAILED.value
            job.error_code = "JOB_ENQUEUE_FAILED"
            job.error_message = str(exc)
            try:
                self.repository.save(job)
            except SQLAlchemyError:
                self.repository.rollback()
            raise errors.job_enqueue_failed({"enqueue": [str(exc)]}) from exc

        job.celery_task_id = task_result.id
        self.repository.save(job)
        return job

    @staticmethod
    def _detail_payload(appeal, student, exam, submission, answer, question) -> dict:
        return {
            "id": str(appeal.id),
            "student_id": str(student.id),
            "student_full_name": student.full_name,
            "student_email": student.email,
            "exam_id": str(exam.id),
            "exam_title": exam.title,
            "submission_id": str(submission.id),
            "answer_id": str(appeal.answer_id) if appeal.answer_id else None,
            "message": appeal.message,
            "status": appeal.status,
            "teacher_response": appeal.teacher_response,
            "old_score": AppealService._decimal_to_string(appeal.old_score),
            "new_score": AppealService._decimal_to_string(appeal.new_score),
            "created_at": appeal.created_at,
            "resolved_at": appeal.resolved_at,
            "total_score": AppealService._decimal_to_string(submission.total_score),
            "max_score": AppealService._decimal_to_string(submission.max_score),
            "needs_review_count": submission.needs_review_count,
            "answer": AppealService._answer_payload(answer, question) if answer is not None and question is not None else None,
        }

    @staticmethod
    def _answer_payload(answer, question) -> dict:
        return {
            "answer_id": str(answer.id),
            "question_id": str(question.id),
            "question_text": question.text,
            "question_type": question.type,
            "student_answer": answer.student_answer,
            "answer_data": answer.answer_data,
            "correct_answer": question.correct_answer,
            "correct_answer_data": question.correct_answer_data,
            "expected_answer": question.expected_answer,
            "current_score": AppealService._decimal_to_string(answer.final_score),
            "max_score": AppealService._decimal_to_string(answer.max_score),
            "ai_feedback": safe_ai_feedback(answer.ai_feedback),
            "teacher_feedback": answer.teacher_feedback,
            "ai_confidence": AppealService._decimal_to_string(answer.ai_confidence),
        }

    @staticmethod
    def _decimal_to_string(value) -> str | None:
        return str(value) if value is not None else None
