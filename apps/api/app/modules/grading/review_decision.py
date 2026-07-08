from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import ExamStatus, QuestionStatus
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import JobType
from app.modules.notifications.constants import EmailType
from app.modules.notifications.models import EmailLog
from app.modules.notifications.service import NotificationService
from app.modules.questions.models import Question
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus


class ReviewDecisionService:
    RELEVANT_SUBMISSION_STATUSES = {
        SubmissionStatus.SUBMITTED.value,
        SubmissionStatus.AUTO_GRADED.value,
        SubmissionStatus.NEEDS_REVIEW.value,
        SubmissionStatus.TEACHER_REVIEWED.value,
        SubmissionStatus.APPROVED.value,
        SubmissionStatus.PUBLISHED.value,
    }
    GRADED_SUBMISSION_STATUSES = {
        SubmissionStatus.AUTO_GRADED.value,
        SubmissionStatus.NEEDS_REVIEW.value,
        SubmissionStatus.TEACHER_REVIEWED.value,
        SubmissionStatus.APPROVED.value,
        SubmissionStatus.PUBLISHED.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def evaluate_submission(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        submission_id: UUID,
    ) -> dict[str, Any]:
        submission = self.db.scalar(
            select(Submission).where(
                Submission.id == submission_id,
                Submission.teacher_id == teacher_id,
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.deleted_at.is_(None),
            )
        )
        if submission is None:
            raise ValueError("Submission not found or mismatched.")

        questions = self._confirmed_questions(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
        )
        answers = self._active_answers(submission)
        self._recalculate_submission(submission, questions, answers)
        self.db.add(submission)
        self.db.commit()

        exam_result = self.evaluate_exam(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
        )
        return {
            "submission_id": str(submission.id),
            "submission_status": submission.status,
            "total_score": str(submission.total_score) if submission.total_score is not None else None,
            "max_score": str(submission.max_score) if submission.max_score is not None else None,
            "needs_review_count": submission.needs_review_count,
            "exam": exam_result,
        }

    def evaluate_exam(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
    ) -> dict[str, Any]:
        exam = self.db.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.teacher_id == teacher_id,
                Exam.class_id == class_id,
                Exam.deleted_at.is_(None),
            )
        )
        if exam is None:
            raise ValueError("Exam not found or mismatched.")

        submissions = list(
            self.db.scalars(
                select(Submission).where(
                    Submission.exam_id == exam_id,
                    Submission.teacher_id == teacher_id,
                    Submission.class_id == class_id,
                    Submission.deleted_at.is_(None),
                    Submission.status.in_(self.RELEVANT_SUBMISSION_STATUSES),
                )
            ).all()
        )
        if not submissions:
            return {
                "exam_id": str(exam.id),
                "exam_status": exam.status,
                "submitted_count": 0,
                "email_queued": False,
            }

        if any(submission.status not in self.GRADED_SUBMISSION_STATUSES for submission in submissions):
            return {
                "exam_id": str(exam.id),
                "exam_status": exam.status,
                "submitted_count": len(submissions),
                "email_queued": False,
            }

        if exam.status == ExamStatus.REVIEW_REQUIRED.value:
            return {
                "exam_id": str(exam.id),
                "exam_status": exam.status,
                "submitted_count": len(submissions),
                "email_queued": False,
            }

        email_already_exists = self._teacher_review_ready_email_exists(exam.id)
        exam.status = ExamStatus.REVIEW_REQUIRED.value
        self.db.add(exam)
        self.db.commit()

        email_job = None
        if not email_already_exists:
            teacher = self._teacher(teacher_id)
            classroom = self._classroom(class_id, teacher_id)
            email_job = NotificationService(self.db).enqueue_teacher_review_ready_email(
                to_email=teacher.email,
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                template_payload=self._teacher_review_ready_payload(
                    teacher=teacher,
                    classroom=classroom,
                    exam=exam,
                    submitted_count=len(submissions),
                    needs_review_count=sum(submission.needs_review_count for submission in submissions),
                ),
            )

        return {
            "exam_id": str(exam.id),
            "exam_status": exam.status,
            "submitted_count": len(submissions),
            "email_queued": email_job is not None,
            "email_job_id": str(email_job.id) if email_job is not None else None,
        }

    def _confirmed_questions(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
    ) -> list[Question]:
        return list(
            self.db.scalars(
                select(Question).where(
                    Question.teacher_id == teacher_id,
                    Question.class_id == class_id,
                    Question.exam_id == exam_id,
                    Question.deleted_at.is_(None),
                    Question.teacher_confirmed.is_(True),
                    Question.status == QuestionStatus.CONFIRMED.value,
                )
            ).all()
        )

    def _active_answers(self, submission: Submission) -> list[Answer]:
        return list(
            self.db.scalars(
                select(Answer).where(
                    Answer.submission_id == submission.id,
                    Answer.teacher_id == submission.teacher_id,
                    Answer.class_id == submission.class_id,
                    Answer.exam_id == submission.exam_id,
                    Answer.student_id == submission.student_id,
                    Answer.deleted_at.is_(None),
                )
            ).all()
        )

    @staticmethod
    def _recalculate_submission(
        submission: Submission,
        questions: list[Question],
        answers: list[Answer],
    ) -> None:
        confirmed_question_ids = {question.id for question in questions}
        answered_question_ids = {answer.question_id for answer in answers}

        submission.max_score = sum((Decimal(question.points) for question in questions), Decimal("0"))
        submission.total_score = sum(
            (answer.final_score for answer in answers if answer.final_score is not None),
            Decimal("0"),
        )
        submission.needs_review_count = sum(1 for answer in answers if answer.needs_review)

        if submission.needs_review_count > 0:
            submission.status = SubmissionStatus.NEEDS_REVIEW.value
            return

        has_all_confirmed_answers = confirmed_question_ids.issubset(answered_question_ids)
        all_answers_scored = bool(answers) and all(answer.final_score is not None for answer in answers)
        if questions and has_all_confirmed_answers and all_answers_scored:
            submission.status = SubmissionStatus.AUTO_GRADED.value
            return

        if submission.status in {
            SubmissionStatus.SUBMITTED.value,
            SubmissionStatus.AUTO_GRADED.value,
            SubmissionStatus.NEEDS_REVIEW.value,
        }:
            submission.status = SubmissionStatus.SUBMITTED.value

    def _teacher_review_ready_email_exists(self, exam_id: UUID) -> bool:
        email_log = self.db.scalar(
            select(EmailLog)
            .where(
                EmailLog.exam_id == exam_id,
                EmailLog.type == EmailType.TEACHER_REVIEW_READY.value,
            )
            .limit(1)
        )
        if email_log is not None:
            return True

        jobs = list(
            self.db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == exam_id,
                    JobLog.job_type == JobType.EMAIL_SEND.value,
                )
            ).all()
        )
        return any(
            isinstance(job.payload_json, dict)
            and job.payload_json.get("email_type") == EmailType.TEACHER_REVIEW_READY.value
            for job in jobs
        )

    def _teacher(self, teacher_id: UUID) -> User:
        teacher = self.db.scalar(
            select(User).where(
                User.id == teacher_id,
                User.deleted_at.is_(None),
            )
        )
        if teacher is None:
            raise ValueError("Teacher not found or mismatched.")
        return teacher

    def _classroom(self, class_id: UUID, teacher_id: UUID) -> Classroom:
        classroom = self.db.scalar(
            select(Classroom).where(
                Classroom.id == class_id,
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
        )
        if classroom is None:
            raise ValueError("Class not found or mismatched.")
        return classroom

    @staticmethod
    def _teacher_review_ready_payload(
        *,
        teacher: User,
        classroom: Classroom,
        exam: Exam,
        submitted_count: int,
        needs_review_count: int,
    ) -> dict[str, Any]:
        review_link = (
            f"{settings.FRONTEND_BASE_URL}/dashboard/classes/"
            f"{classroom.id}/exams/{exam.id}/review"
        )
        return {
            "teacher_full_name": teacher.full_name,
            "teacher_name": teacher.full_name,
            "class_title": classroom.title,
            "exam_title": exam.title,
            "review_link": review_link,
            "submitted_count": submitted_count,
            "submission_count": submitted_count,
            "needs_review_count": needs_review_count,
        }
