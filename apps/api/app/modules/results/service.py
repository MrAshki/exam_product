from __future__ import annotations

import secrets
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from celery import Celery
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.exams.status import ExamStatus
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE, LEADERBOARD_QUEUE, JobStatus, JobType
from app.modules.notifications.constants import EmailType
from app.modules.results import errors
from app.modules.results.models import LeaderboardToken, ResultToken
from app.modules.results.repository import ResultsRepository
from app.modules.students.models import Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus


EMAIL_SEND_TASK_NAME = "apps.worker.tasks.email_tasks.send_email"
LEADERBOARD_UPDATE_TASK_NAME = "apps.worker.tasks.leaderboard_tasks.update_leaderboard"


class PublishResultsService:
    PUBLISHABLE_SUBMISSION_STATUSES = {SubmissionStatus.APPROVED.value, SubmissionStatus.PUBLISHED.value}

    def __init__(self, db: Session) -> None:
        self.repository = ResultsRepository(db)
        self.celery_app = Celery(
            "class_centric_exam_api",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )

    def publish_results(self, class_id: UUID, exam_id: UUID, teacher: User) -> dict:
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise errors.class_not_found()
        exam = self.repository.get_exam_for_teacher_class(class_id, exam_id, teacher.id)
        if exam is None:
            raise errors.exam_not_found()
        if exam.status not in {ExamStatus.APPROVED.value, ExamStatus.PUBLISHED.value}:
            raise errors.exam_not_approved({"status": exam.status})

        all_submissions = self.repository.list_publishable_submissions(class_id, exam_id, teacher.id)
        submissions = [
            submission
            for submission in all_submissions
            if submission.status in self.PUBLISHABLE_SUBMISSION_STATUSES
        ]
        if not submissions:
            raise errors.no_approved_submissions()

        self._validate_publishable_results(class_id, exam_id, teacher.id, submissions)
        leaderboard_token = self._get_or_create_leaderboard_token(exam) if exam.show_leaderboard else None

        now = datetime.now(timezone.utc)
        result_token_pairs: list[tuple[Submission, Student, ResultToken, bool]] = []
        created_result_tokens = 0
        for submission in submissions:
            student = self.repository.get_student(submission.student_id, teacher.id)
            if student is None:
                raise errors.results_incomplete({"students": [str(submission.student_id)]})

            result_token = self.repository.get_result_token_for_submission(submission.id)
            created = False
            if result_token is None:
                result_token = self.repository.create_result_token(submission, self._generate_token())
                created = True
                created_result_tokens += 1
            result_token_pairs.append((submission, student, result_token, created))
            submission.status = SubmissionStatus.PUBLISHED.value
            submission.published_at = submission.published_at or now

        exam.status = ExamStatus.PUBLISHED.value
        try:
            self.repository.save(exam, *[pair[0] for pair in result_token_pairs])
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise errors.results_incomplete({"database": [str(exc)]}) from exc

        queued_result_emails = 0
        for submission, student, result_token, _created in result_token_pairs:
            if self._result_email_already_queued(result_token.id):
                continue
            self._enqueue_result_email(
                teacher=teacher,
                classroom_title=classroom.title,
                exam_title=exam.title,
                student=student,
                submission=submission,
                result_token=result_token,
                leaderboard_token=leaderboard_token,
            )
            queued_result_emails += 1

        if leaderboard_token is not None and not self._leaderboard_job_already_queued(exam.id):
            self._enqueue_leaderboard_update(teacher.id, class_id, exam_id)

        return {
            "exam_id": str(exam.id),
            "status": exam.status,
            "created_result_tokens": created_result_tokens,
            "leaderboard_enabled": bool(exam.show_leaderboard),
            "queued_result_emails": queued_result_emails,
        }

    def get_public_result(self, token: str) -> dict:
        if not token:
            raise errors.invalid_result_token()
        context = self.repository.get_published_result_context(token)
        if context is None:
            raise errors.invalid_result_token()
        _result_token, exam, classroom, student, submission = context
        if exam.status != ExamStatus.PUBLISHED.value or submission.published_at is None:
            raise errors.result_not_published()

        answer_rows = self.repository.list_result_answer_rows(submission)
        return {
            "student_full_name": student.full_name,
            "class_title": classroom.title,
            "exam_title": exam.title,
            "total_score": self._decimal_to_string(submission.total_score),
            "max_score": self._decimal_to_string(submission.max_score),
            "answers": [self._result_answer_payload(answer, question, exam) for answer, question in answer_rows],
            "can_appeal": bool(exam.allow_appeals and exam.status == ExamStatus.PUBLISHED.value),
        }

    def get_public_leaderboard(self, token: str) -> dict:
        if not token:
            raise errors.invalid_leaderboard_token()
        context = self.repository.get_leaderboard_context(token)
        if context is None:
            raise errors.invalid_leaderboard_token()
        _leaderboard_token, exam, classroom = context
        if exam.status != ExamStatus.PUBLISHED.value:
            raise errors.leaderboard_not_available()
        if not exam.show_leaderboard:
            raise errors.leaderboard_not_available()

        rows = self.repository.list_leaderboard_rows(exam.class_id, exam.id)
        items = []
        for index, (submission, student) in enumerate(rows, start=1):
            percentage = None
            if submission.total_score is not None and submission.max_score not in (None, Decimal("0")):
                percentage = float((submission.total_score / submission.max_score) * Decimal("100"))
            items.append(
                {
                    "rank": index,
                    "student_full_name": student.full_name,
                    "score": self._decimal_to_string(submission.total_score),
                    "max_score": self._decimal_to_string(submission.max_score),
                    "percentage": percentage,
                }
            )
        return {
            "class_title": classroom.title,
            "exam_title": exam.title,
            "items": items,
        }

    def _validate_publishable_results(
        self,
        class_id: UUID,
        exam_id: UUID,
        teacher_id: UUID,
        submissions: list[Submission],
    ) -> None:
        questions = self.repository.list_confirmed_questions(class_id, exam_id, teacher_id)
        if not questions:
            raise errors.results_incomplete({"questions": ["No confirmed questions exist."]})
        question_ids = {question.id for question in questions}
        missing: dict[str, list[str]] = {}
        for submission in submissions:
            answers = self.repository.list_answers_for_submission(submission)
            answers_by_question_id = {answer.question_id: answer for answer in answers}
            for question_id in question_ids:
                answer = answers_by_question_id.get(question_id)
                if answer is None or answer.final_score is None:
                    missing.setdefault("final_scores", []).append(str(submission.id))
                    break
        if missing:
            raise errors.results_incomplete(missing)

    def _get_or_create_leaderboard_token(self, exam) -> LeaderboardToken:
        leaderboard_token = self.repository.get_leaderboard_token_for_exam(exam.class_id, exam.id)
        if leaderboard_token is not None:
            return leaderboard_token
        return self.repository.create_leaderboard_token(exam, self._generate_token())

    def _enqueue_result_email(
        self,
        *,
        teacher: User,
        classroom_title: str,
        exam_title: str,
        student: Student,
        submission: Submission,
        result_token: ResultToken,
        leaderboard_token: LeaderboardToken | None,
    ) -> None:
        result_link = f"{settings.FRONTEND_BASE_URL}/result/{result_token.token}"
        leaderboard_link = (
            f"{settings.FRONTEND_BASE_URL}/leaderboard/{leaderboard_token.token}"
            if leaderboard_token is not None
            else None
        )
        payload = {
            "email_type": EmailType.STUDENT_RESULT_PUBLISHED.value,
            "teacher_id": str(teacher.id),
            "class_id": str(submission.class_id),
            "exam_id": str(submission.exam_id),
            "student_id": str(student.id),
            "to_email": student.email,
            "template_payload": {
                "student_full_name": student.full_name,
                "class_title": classroom_title,
                "exam_title": exam_title,
                "total_score": self._decimal_to_string(submission.total_score),
                "max_score": self._decimal_to_string(submission.max_score),
                "result_link": result_link,
                "leaderboard_link": leaderboard_link,
            },
        }
        job = JobLog(
            teacher_id=teacher.id,
            class_id=submission.class_id,
            exam_id=submission.exam_id,
            job_type=JobType.EMAIL_SEND.value,
            queue_name=EMAIL_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="result_token",
            entity_id=result_token.id,
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

    def _result_email_already_queued(self, result_token_id: UUID) -> bool:
        db = self.repository.db
        from sqlalchemy import select

        return (
            db.scalar(
                select(JobLog.id).where(
                    JobLog.job_type == JobType.EMAIL_SEND.value,
                    JobLog.queue_name == EMAIL_QUEUE,
                    JobLog.entity_type == "result_token",
                    JobLog.entity_id == result_token_id,
                )
            )
            is not None
        )

    def _leaderboard_job_already_queued(self, exam_id: UUID) -> bool:
        db = self.repository.db
        from sqlalchemy import select

        return (
            db.scalar(
                select(JobLog.id).where(
                    JobLog.job_type == JobType.LEADERBOARD_UPDATE.value,
                    JobLog.queue_name == LEADERBOARD_QUEUE,
                    JobLog.entity_type == "exam",
                    JobLog.entity_id == exam_id,
                )
            )
            is not None
        )

    def _generate_token(self) -> str:
        for _ in range(10):
            token = secrets.token_urlsafe(32)
            if not self.repository.token_value_exists(token):
                return token
        raise errors.results_incomplete({"token": ["Unable to generate a unique token."]})

    @staticmethod
    def _result_answer_payload(answer: Answer, question, exam) -> dict:
        return {
            "question_text": question.text,
            "question_type": question.type,
            "student_answer": answer.student_answer,
            "answer_data": answer.answer_data,
            "correct_answer": question.correct_answer if exam.show_correct_answers else None,
            "correct_answer_data": question.correct_answer_data if exam.show_correct_answers else None,
            "final_score": PublishResultsService._decimal_to_string(answer.final_score),
            "max_score": PublishResultsService._decimal_to_string(answer.max_score),
            "feedback": answer.ai_feedback if exam.show_feedback else None,
        }

    @staticmethod
    def _decimal_to_string(value) -> str | None:
        return str(value) if value is not None else None
