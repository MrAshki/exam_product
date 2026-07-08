from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from apps.worker.shared.worker_context import worker_db_session
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import QuestionType
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import JobStatus
from app.modules.questions.models import Question
from app.modules.students.models import Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus


class DeterministicGradingWorkerService:
    def run(self, payload: dict) -> dict:
        job_id = payload["job_id"]
        job_uuid = UUID(job_id)

        with worker_db_session() as db:
            job = db.scalar(select(JobLog).where(JobLog.id == job_uuid))
            if job is None:
                return {"success": False, "error_message": f"Job log not found: {job_id}"}

            self._mark_running(db, job)
            try:
                result = self._grade(db, job, payload)
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

    def _grade(self, db, job: JobLog, payload: dict) -> dict:
        teacher_id = self._required_uuid(payload, "teacher_id")
        class_id = self._required_uuid(payload, "class_id")
        exam_id = self._required_uuid(payload, "exam_id")
        submission_id = self._required_uuid(payload, "submission_id")

        if job.submission_id is not None and job.submission_id != submission_id:
            raise ValueError("Job submission_id does not match payload.")
        if job.exam_id is not None and job.exam_id != exam_id:
            raise ValueError("Job exam_id does not match payload.")

        submission = db.scalar(
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

        classroom = db.scalar(
            select(Classroom).where(
                Classroom.id == class_id,
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
        )
        if classroom is None:
            raise ValueError("Class not found or mismatched.")

        student = db.scalar(
            select(Student).where(
                Student.id == submission.student_id,
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
            )
        )
        if student is None:
            raise ValueError("Student not found or mismatched.")

        questions = list(
            db.scalars(
                select(Question).where(
                    Question.exam_id == exam_id,
                    Question.class_id == class_id,
                    Question.teacher_id == teacher_id,
                    Question.deleted_at.is_(None),
                    Question.teacher_confirmed.is_(True),
                    Question.status == "confirmed",
                )
            ).all()
        )
        questions_by_id = {question.id: question for question in questions}

        answers = list(
            db.scalars(
                select(Answer).where(
                    Answer.submission_id == submission_id,
                    Answer.teacher_id == teacher_id,
                    Answer.class_id == class_id,
                    Answer.exam_id == exam_id,
                    Answer.student_id == submission.student_id,
                    Answer.deleted_at.is_(None),
                )
            ).all()
        )
        if not answers:
            raise ValueError("Submission has no answers to grade.")

        objective_count = 0
        for answer in answers:
            question = questions_by_id.get(answer.question_id)
            if question is None:
                raise ValueError("Answer question not found or mismatched.")
            if question.type not in {QuestionType.MULTIPLE_CHOICE.value, QuestionType.TRUE_FALSE.value}:
                continue

            calculated_score = self._score_objective_answer(question, answer)
            answer.auto_score = calculated_score
            answer.max_score = Decimal(question.points)
            if answer.teacher_score is None:
                answer.final_score = calculated_score
            elif answer.final_score is None:
                answer.final_score = answer.teacher_score
            answer.needs_review = False
            answer.reviewed_by_teacher = False
            db.add(answer)
            objective_count += 1

        submission.max_score = sum(Decimal(question.points) for question in questions)
        final_scores = [answer.final_score for answer in answers if answer.final_score is not None]
        submission.total_score = sum(final_scores, Decimal("0"))
        submission.needs_review_count = sum(1 for answer in answers if answer.needs_review)
        if questions and all(
            question.type in {QuestionType.MULTIPLE_CHOICE.value, QuestionType.TRUE_FALSE.value}
            for question in questions
        ):
            submission.status = SubmissionStatus.AUTO_GRADED.value
        db.add(submission)
        db.commit()

        return {
            "success": True,
            "graded_answers": objective_count,
            "submission_id": str(submission.id),
            "status": submission.status,
            "total_score": str(submission.total_score) if submission.total_score is not None else None,
            "max_score": str(submission.max_score) if submission.max_score is not None else None,
        }

    @staticmethod
    def _score_objective_answer(question: Question, answer: Answer) -> Decimal:
        if question.type == QuestionType.MULTIPLE_CHOICE.value:
            expected = DeterministicGradingWorkerService._normalize_choice(
                (question.correct_answer_data or {}).get("selected_option")
                if isinstance(question.correct_answer_data, dict)
                else None
            )
            if expected is None:
                expected = DeterministicGradingWorkerService._normalize_choice(question.correct_answer)
            selected = DeterministicGradingWorkerService._normalize_choice(
                (answer.answer_data or {}).get("selected_option")
                if isinstance(answer.answer_data, dict)
                else None
            )
            return Decimal(question.points) if selected is not None and selected == expected else Decimal("0")

        expected_bool = DeterministicGradingWorkerService._normalize_bool(
            (question.correct_answer_data or {}).get("value")
            if isinstance(question.correct_answer_data, dict)
            else None
        )
        if expected_bool is None:
            expected_bool = DeterministicGradingWorkerService._normalize_bool(question.correct_answer)
        selected_bool = DeterministicGradingWorkerService._normalize_bool(
            (answer.answer_data or {}).get("value")
            if isinstance(answer.answer_data, dict)
            else None
        )
        return Decimal(question.points) if selected_bool is not None and selected_bool == expected_bool else Decimal("0")

    @staticmethod
    def _normalize_choice(value) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        return normalized or None

    @staticmethod
    def _normalize_bool(value) -> bool | None:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        return None

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
