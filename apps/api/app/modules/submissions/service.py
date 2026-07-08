from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.exams.models import Exam, ExamToken
from app.modules.exams.status import ExamStatus, QuestionType
from app.modules.grading.service import GradingDispatchService
from app.modules.questions.models import Question, QuestionOption
from app.modules.submissions.errors import (
    exam_already_submitted,
    exam_not_active,
    exam_time_expired,
    invalid_exam_token,
    question_not_confirmed,
    question_not_found,
    submission_not_found,
    submission_not_in_progress,
    validation_error,
)
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.schemas import ExamAnswerSubmit, ExamSubmitRequest
from app.modules.submissions.status import (
    ExamAccessStatus,
    SUBMITTED_OR_LATER_STATUSES,
    SubmissionStatus,
)


class SubmissionService:
    def __init__(self, db: Session) -> None:
        self.repository = SubmissionRepository(db)

    def get_access_state(self, exam_token: str) -> dict:
        token, exam, classroom, student = self._get_token_context(exam_token)
        now = self._now()
        self._ensure_scheduled_exam(exam)
        if self._is_before_start(exam, now):
            status = ExamAccessStatus.WAITING.value
        elif self._is_within_exam_window(exam, now):
            status = ExamAccessStatus.READY.value
        else:
            raise exam_not_active()

        return {
            "status": status,
            "exam_title": exam.title,
            "class_title": classroom.title,
            "student_full_name": student.full_name,
            "start_time": exam.start_time,
            "end_time": exam.end_time,
            "duration_minutes": exam.duration_minutes,
        }

    def start_exam(self, exam_token: str) -> dict:
        token, exam, _classroom, _student = self._get_token_context(exam_token)
        now = self._now()
        self._ensure_exam_active(exam, now)

        submission = self.repository.get_active_submission_for_exam_student(
            exam_id=exam.id,
            student_id=token.student_id,
        )
        if submission is not None:
            if submission.status == SubmissionStatus.IN_PROGRESS.value:
                return self._build_start_response(exam, submission)
            if submission.status in SUBMITTED_OR_LATER_STATUSES:
                raise exam_already_submitted()
            submission.status = SubmissionStatus.IN_PROGRESS.value
            submission.started_at = now
            submission = self.repository.create_or_update_submission(submission)
            return self._build_start_response(exam, submission)

        try:
            submission = self.repository.create_submission(
                teacher_id=token.teacher_id,
                class_id=token.class_id,
                exam_id=token.exam_id,
                student_id=token.student_id,
                token_id=token.id,
                status=SubmissionStatus.IN_PROGRESS.value,
                started_at=now,
            )
        except IntegrityError:
            self.repository.rollback()
            existing_submission = self.repository.get_active_submission_for_exam_student(
                exam_id=exam.id,
                student_id=token.student_id,
            )
            if existing_submission is not None and existing_submission.status == SubmissionStatus.IN_PROGRESS.value:
                return self._build_start_response(exam, existing_submission)
            raise

        return self._build_start_response(exam, submission)

    def submit_exam(self, exam_token: str, payload: ExamSubmitRequest) -> dict:
        token, exam, _classroom, _student = self._get_token_context(exam_token)
        now = self._now()
        self._ensure_scheduled_exam(exam)

        submission = self.repository.get_active_submission_for_exam_student(
            exam_id=exam.id,
            student_id=token.student_id,
        )
        if submission is None:
            raise submission_not_found()
        if submission.status in SUBMITTED_OR_LATER_STATUSES:
            raise exam_already_submitted()
        if submission.status != SubmissionStatus.IN_PROGRESS.value:
            raise submission_not_in_progress()
        if submission.started_at is None:
            raise submission_not_in_progress()
        if now > self._allowed_until(exam, submission):
            raise exam_time_expired()

        questions = self.repository.list_confirmed_questions_for_exam(
            exam_id=exam.id,
            class_id=exam.class_id,
            teacher_id=exam.teacher_id,
        )
        questions_by_id = {question.id: question for question in questions}
        self._validate_submitted_questions(payload.answers, questions_by_id, exam.id)

        answers = [
            Answer(
                teacher_id=token.teacher_id,
                class_id=token.class_id,
                exam_id=token.exam_id,
                student_id=token.student_id,
                submission_id=submission.id,
                question_id=answer_payload.question_id,
                student_answer=answer_payload.student_answer,
                answer_data=answer_payload.answer_data,
                max_score=Decimal(questions_by_id[answer_payload.question_id].points),
            )
            for answer_payload in payload.answers
        ]
        submission.status = SubmissionStatus.SUBMITTED.value
        submission.submitted_at = now
        submission.max_score = Decimal(exam.total_points)

        try:
            saved_submission = self.repository.save_submission_with_answers(submission, answers)
        except IntegrityError:
            self.repository.rollback()
            raise validation_error({"answers": ["Duplicate answers are not allowed."]}) from None

        # Phase 11B will add AI grading dispatch for subjective answers.
        GradingDispatchService(self.repository.db).enqueue_deterministic_grading(
            teacher_id=token.teacher_id,
            class_id=token.class_id,
            exam_id=token.exam_id,
            submission_id=saved_submission.id,
        )

        return {
            "submission_id": saved_submission.id,
            "status": saved_submission.status,
            "submitted_at": saved_submission.submitted_at,
            "saved_answers": len(answers),
        }

    def create_submission(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        student_id: UUID,
        token_id: UUID,
        status: str = SubmissionStatus.NOT_STARTED.value,
        max_score: Decimal | None = None,
    ) -> Submission:
        return self.repository.create_submission(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            token_id=token_id,
            status=status,
            max_score=max_score,
        )

    def create_answer(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        student_id: UUID,
        submission_id: UUID,
        question_id: UUID,
        student_answer: str | None = None,
        answer_data: dict | list | None = None,
        max_score: Decimal | None = None,
    ) -> Answer:
        return self.repository.create_answer(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            submission_id=submission_id,
            question_id=question_id,
            student_answer=student_answer,
            answer_data=answer_data,
            max_score=max_score,
        )

    def list_answers_by_submission(self, submission_id: UUID) -> list[Answer]:
        return self.repository.list_answers_by_submission(submission_id)

    def _get_token_context(self, exam_token: str):
        context = self.repository.get_valid_token_context(exam_token)
        if context is None:
            raise invalid_exam_token()
        return context

    @staticmethod
    def _ensure_scheduled_exam(exam: Exam) -> None:
        if exam.status != ExamStatus.SCHEDULED.value:
            raise exam_not_active()
        if exam.start_time is None or exam.end_time is None or exam.duration_minutes is None:
            raise exam_not_active()

    def _ensure_exam_active(self, exam: Exam, now: datetime) -> None:
        self._ensure_scheduled_exam(exam)
        if not self._is_within_exam_window(exam, now):
            raise exam_not_active()

    @staticmethod
    def _is_before_start(exam: Exam, now: datetime) -> bool:
        return exam.start_time is not None and now < SubmissionService._as_aware(exam.start_time)

    @staticmethod
    def _is_within_exam_window(exam: Exam, now: datetime) -> bool:
        if exam.start_time is None or exam.end_time is None:
            return False
        return SubmissionService._as_aware(exam.start_time) <= now <= SubmissionService._as_aware(exam.end_time)

    def _build_start_response(self, exam: Exam, submission: Submission) -> dict:
        if submission.started_at is None:
            raise submission_not_in_progress()
        questions = self.repository.list_confirmed_questions_for_exam(
            exam_id=exam.id,
            class_id=exam.class_id,
            teacher_id=exam.teacher_id,
        )
        options = self.repository.list_options_for_questions([question.id for question in questions])
        return {
            "submission_id": submission.id,
            "started_at": submission.started_at,
            "allowed_until": self._allowed_until(exam, submission),
            "questions": self._student_question_payloads(questions, options),
        }

    @staticmethod
    def _student_question_payloads(
        questions: list[Question],
        options: list[QuestionOption],
    ) -> list[dict]:
        options_by_question_id: dict[UUID, list[QuestionOption]] = defaultdict(list)
        for option in options:
            options_by_question_id[option.question_id].append(option)

        payloads = []
        for question in questions:
            question_payload = {
                "id": question.id,
                "order_index": question.order_index,
                "type": question.type,
                "text": question.text or "",
                "points": question.points,
                "options": [],
            }
            if question.type == QuestionType.MULTIPLE_CHOICE.value:
                question_payload["options"] = [
                    {
                        "option_key": option.option_key,
                        "option_text": option.option_text,
                    }
                    for option in options_by_question_id.get(question.id, [])
                ]
            payloads.append(question_payload)
        return payloads

    def _validate_submitted_questions(
        self,
        submitted_answers: list[ExamAnswerSubmit],
        questions_by_id: dict[UUID, Question],
        exam_id: UUID,
    ) -> None:
        seen_question_ids: set[UUID] = set()
        for answer in submitted_answers:
            if answer.question_id in seen_question_ids:
                raise validation_error({"answers": ["Duplicate question_id values are not allowed."]})
            seen_question_ids.add(answer.question_id)
            question = questions_by_id.get(answer.question_id)
            if question is None:
                active_question = self.repository.get_active_question_by_id(answer.question_id)
                if active_question is not None and active_question.exam_id == exam_id:
                    raise question_not_confirmed({"question_id": str(answer.question_id)})
                raise question_not_found({"question_id": str(answer.question_id)})

    @staticmethod
    def _allowed_until(exam: Exam, submission: Submission) -> datetime:
        if submission.started_at is None or exam.end_time is None or exam.duration_minutes is None:
            raise submission_not_in_progress()
        started_at = SubmissionService._as_aware(submission.started_at)
        exam_end = SubmissionService._as_aware(exam.end_time)
        return min(exam_end, started_at + timedelta(minutes=exam.duration_minutes))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _as_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
