from __future__ import annotations

import secrets
from collections import defaultdict
from datetime import timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.exams.errors import (
    blueprint_not_found,
    class_not_found,
    email_send_failed,
    exam_already_scheduled,
    exam_already_has_blueprint,
    exam_not_draft,
    exam_not_found,
    exam_not_ready,
    exam_not_scheduled,
    exam_requires_students,
    exam_title_already_exists,
    validation_error,
)
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.repository import ExamRepository
from app.modules.exams.schemas import (
    BlueprintCreate,
    BlueprintUpdate,
    ExamCreate,
    ExamInvitationRequest,
    ExamScheduleRequest,
    ExamUpdate,
)
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.notifications.constants import EmailType
from app.modules.notifications.service import NotificationService
from app.modules.questions.models import Question, QuestionOption
from app.modules.students.models import Student


class ExamService:
    def __init__(self, db: Session) -> None:
        self.repository = ExamRepository(db)

    def create(self, class_id: UUID, payload: ExamCreate, teacher: User) -> Exam:
        self._ensure_class_owned(class_id, teacher)
        if not self.repository.class_has_active_students(class_id, teacher.id):
            raise exam_requires_students()

        title = payload.title.strip()
        if self.repository.get_by_title_for_class(title, class_id, teacher.id):
            raise exam_title_already_exists()

        exam = Exam(
            teacher_id=teacher.id,
            class_id=class_id,
            title=title,
            description=self._clean_optional(payload.description),
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_minutes=payload.duration_minutes,
            status=ExamStatus.DRAFT.value,
            total_points=payload.total_points,
            show_leaderboard=payload.show_leaderboard,
            allow_appeals=payload.allow_appeals,
            show_correct_answers=payload.show_correct_answers,
            show_feedback=payload.show_feedback,
        )

        try:
            return self.repository.create(exam)
        except IntegrityError:
            self.repository.rollback()
            raise exam_title_already_exists() from None

    def list(self, class_id: UUID, teacher: User) -> list[Exam]:
        self._ensure_class_owned(class_id, teacher)
        return self.repository.list_by_class_for_teacher(class_id, teacher.id)

    def get(self, class_id: UUID, exam_id: UUID, teacher: User) -> Exam:
        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        return exam

    def update(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: ExamUpdate,
        teacher: User,
    ) -> Exam:
        exam = self.get(class_id, exam_id, teacher)
        update_data = payload.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"] is not None:
            title = update_data["title"].strip()
            duplicate = self.repository.get_by_title_for_class(
                title,
                class_id,
                teacher.id,
                exclude_exam_id=exam.id,
            )
            if duplicate is not None:
                raise exam_title_already_exists()
            exam.title = title

        for field_name in [
            "start_time",
            "end_time",
            "duration_minutes",
            "total_points",
            "show_leaderboard",
            "allow_appeals",
            "show_correct_answers",
            "show_feedback",
        ]:
            if field_name in update_data:
                setattr(exam, field_name, update_data[field_name])

        if "description" in update_data:
            exam.description = self._clean_optional(update_data["description"])

        try:
            return self.repository.save(exam)
        except IntegrityError:
            self.repository.rollback()
            raise exam_title_already_exists() from None

    def delete(self, class_id: UUID, exam_id: UUID, teacher: User) -> None:
        exam = self.get(class_id, exam_id, teacher)
        self.repository.soft_delete_exam_tree(exam)

    def schedule(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: ExamScheduleRequest,
        teacher: User,
    ) -> dict:
        self._ensure_schedule_window(payload)
        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        if exam.status == ExamStatus.SCHEDULED.value:
            raise exam_already_scheduled()
        self._ensure_exam_is_draft(exam)

        students = self.repository.list_active_students_for_class(class_id, teacher.id)
        if not students:
            raise exam_not_ready({"students": ["Class must have at least one active student."]})
        self._validate_exam_ready(exam, students, teacher)

        exam.start_time = payload.start_time
        exam.end_time = payload.end_time
        exam.duration_minutes = payload.duration_minutes
        exam.status = ExamStatus.SCHEDULED.value
        tokens = self._build_missing_tokens(exam, students)

        try:
            saved_exam = self.repository.save_exam_with_tokens(exam, tokens)
        except IntegrityError:
            self.repository.rollback()
            raise exam_not_ready({"exam_tokens": ["Exam tokens could not be created."]}) from None

        return {
            "id": saved_exam.id,
            "status": saved_exam.status,
            "start_time": saved_exam.start_time,
            "end_time": saved_exam.end_time,
            "duration_minutes": saved_exam.duration_minutes,
            "created_exam_tokens": len(tokens),
        }

    def send_invitations(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: ExamInvitationRequest,
        teacher: User,
    ) -> dict:
        if not payload.send_to_all:
            raise validation_error({"send_to_all": ["Only send_to_all=true is supported in this phase."]})

        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        if exam.status != ExamStatus.SCHEDULED.value:
            raise exam_not_scheduled()

        students = self.repository.list_active_students_for_class(class_id, teacher.id)
        if not students:
            raise exam_not_ready({"students": ["Class must have at least one active student."]})

        self._ensure_tokens_for_active_students(exam, students)
        tokens_by_student_id = {
            token.student_id: token
            for token in self.repository.list_active_tokens_for_exam(exam.id, class_id, teacher.id)
        }

        notification_service = NotificationService(self.repository.db)
        queued_emails = 0
        for student in students:
            token = tokens_by_student_id.get(student.id)
            if token is None:
                raise exam_not_ready({"exam_tokens": ["Missing exam token for an active student."]})
            try:
                notification_service.enqueue_email(
                    email_type=EmailType.EXAM_INVITATION.value,
                    teacher_id=teacher.id,
                    class_id=class_id,
                    exam_id=exam.id,
                    student_id=student.id,
                    to_email=student.email,
                    template_payload=self._build_invitation_payload(
                        exam=exam,
                        student=student,
                        teacher=teacher,
                        token=token,
                    ),
                )
            except Exception as exc:
                raise email_send_failed({"student_id": str(student.id), "email": student.email}) from exc
            queued_emails += 1

        return {"queued_emails": queued_emails}

    def create_blueprint(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: BlueprintCreate,
        teacher: User,
    ) -> ExamBlueprint:
        exam = self.get(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        if self.repository.get_blueprint_for_exam(exam.id, class_id, teacher.id):
            raise exam_already_has_blueprint()

        blueprint = self._build_blueprint(class_id, exam_id, payload, teacher)
        questions = self._build_question_slots(class_id, exam_id, teacher, payload)

        try:
            return self.repository.create_blueprint_with_slots(blueprint, questions)
        except IntegrityError:
            self.repository.rollback()
            raise exam_already_has_blueprint() from None

    def get_blueprint(self, class_id: UUID, exam_id: UUID, teacher: User) -> ExamBlueprint:
        exam = self.get(class_id, exam_id, teacher)
        blueprint = self.repository.get_blueprint_for_exam(exam.id, class_id, teacher.id)
        if blueprint is None:
            raise blueprint_not_found()
        return blueprint

    def update_blueprint(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: BlueprintUpdate,
        teacher: User,
    ) -> ExamBlueprint:
        exam = self.get(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        blueprint = self.repository.get_blueprint_for_exam(exam.id, class_id, teacher.id)
        if blueprint is None:
            raise blueprint_not_found()
        if self.repository.has_confirmed_questions(exam.id, class_id, teacher.id):
            raise exam_not_draft()

        self._apply_blueprint_counts(blueprint, payload)
        questions = self._build_question_slots(class_id, exam_id, teacher, payload)

        try:
            return self.repository.update_blueprint_and_recreate_slots(blueprint, questions)
        except IntegrityError:
            self.repository.rollback()
            raise exam_already_has_blueprint() from None

    def _ensure_class_owned(self, class_id: UUID, teacher: User) -> None:
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()

    @staticmethod
    def _ensure_exam_is_draft(exam: Exam) -> None:
        if exam.status != ExamStatus.DRAFT.value:
            raise exam_not_draft()

    @staticmethod
    def _ensure_schedule_window(payload: ExamScheduleRequest) -> None:
        if payload.start_time >= payload.end_time:
            raise validation_error({"end_time": ["End time must be after start time."]})
        window_minutes = (payload.end_time - payload.start_time) / timedelta(minutes=1)
        if payload.duration_minutes > window_minutes:
            raise validation_error(
                {"duration_minutes": ["Duration must not exceed the scheduled time window."]}
            )

    def _validate_exam_ready(self, exam: Exam, students: list[Student], teacher: User) -> None:
        errors: dict[str, list[str]] = {}
        blueprint = self.repository.get_blueprint_for_exam(exam.id, exam.class_id, teacher.id)
        if blueprint is None:
            errors.setdefault("blueprint", []).append("Blueprint is required.")

        questions = self.repository.list_questions_for_exam(exam.id, exam.class_id, teacher.id)
        if not questions:
            errors.setdefault("questions", []).append("Question slots are required.")
        elif blueprint is not None and len(questions) != blueprint.total_question_count:
            errors.setdefault("questions", []).append("Question slot count must match the blueprint.")

        options_by_question_id = self._options_by_question_id(
            self.repository.list_options_for_exam(exam.id, exam.class_id, teacher.id)
        )
        for question in questions:
            self._validate_question_ready(question, options_by_question_id.get(question.id, []), errors)

        total_points = sum(question.points for question in questions)
        if total_points != exam.total_points:
            errors.setdefault("total_points", []).append("Question points must equal exam total points.")

        if not students:
            errors.setdefault("students", []).append("Class must have at least one active student.")

        if errors:
            raise exam_not_ready(errors)

    def _validate_question_ready(
        self,
        question: Question,
        options: list[QuestionOption],
        errors: dict[str, list[str]],
    ) -> None:
        key = f"question_{question.order_index}"
        if question.status != QuestionStatus.CONFIRMED.value or not question.teacher_confirmed:
            errors.setdefault(key, []).append("Question must be teacher confirmed.")
        if question.needs_teacher_review:
            errors.setdefault(key, []).append("Question must not need teacher review.")
        if question.status in {
            QuestionStatus.EMPTY.value,
            QuestionStatus.DRAFT.value,
            QuestionStatus.EXTRACTED.value,
        }:
            errors.setdefault(key, []).append("Question must not be empty, draft, or extracted.")
        if not question.text:
            errors.setdefault(key, []).append("Question text is required.")
        if question.points <= 0:
            errors.setdefault(key, []).append("Question points must be greater than 0.")

        if question.type == QuestionType.MULTIPLE_CHOICE.value:
            self._validate_multiple_choice_ready(question, options, errors, key)
        elif question.type == QuestionType.TRUE_FALSE.value:
            if question.correct_answer not in {"true", "false"}:
                errors.setdefault(key, []).append("True/false question requires a correct answer.")
        elif question.type == QuestionType.SHORT_ANSWER.value:
            if not question.expected_answer:
                errors.setdefault(key, []).append("Short answer question requires an expected answer.")
        elif question.type == QuestionType.ESSAY.value:
            if not question.expected_answer:
                errors.setdefault(key, []).append("Essay question requires an expected answer.")
            if not question.rubric_teacher_confirmed:
                errors.setdefault(key, []).append("Essay rubric must be teacher confirmed.")
        else:
            errors.setdefault(key, []).append("Question type is not supported.")

    @staticmethod
    def _validate_multiple_choice_ready(
        question: Question,
        options: list[QuestionOption],
        errors: dict[str, list[str]],
        key: str,
    ) -> None:
        if len(options) < 2:
            errors.setdefault(key, []).append("Multiple choice question requires at least 2 options.")
        correct_options = [option for option in options if option.is_correct]
        if len(correct_options) != 1:
            errors.setdefault(key, []).append("Multiple choice question requires exactly one correct option.")
        if not question.correct_answer:
            errors.setdefault(key, []).append("Multiple choice question requires a correct answer.")
        elif correct_options and question.correct_answer.strip().lower() != correct_options[0].option_key.strip().lower():
            errors.setdefault(key, []).append("Correct answer must match the correct option key.")

    @staticmethod
    def _options_by_question_id(
        options: list[QuestionOption],
    ) -> dict[UUID, list[QuestionOption]]:
        grouped: dict[UUID, list[QuestionOption]] = defaultdict(list)
        for option in options:
            grouped[option.question_id].append(option)
        return grouped

    def _ensure_tokens_for_active_students(self, exam: Exam, students: list[Student]) -> None:
        tokens = self._build_missing_tokens(exam, students)
        if not tokens:
            return
        try:
            self.repository.create_tokens(tokens)
        except IntegrityError:
            self.repository.rollback()
            raise exam_not_ready({"exam_tokens": ["Exam tokens could not be created."]}) from None

    def _build_missing_tokens(self, exam: Exam, students: list[Student]) -> list[ExamToken]:
        active_tokens = self.repository.list_active_tokens_for_exam(
            exam_id=exam.id,
            class_id=exam.class_id,
            teacher_id=exam.teacher_id,
        )
        existing_student_ids = {token.student_id for token in active_tokens}
        return [
            ExamToken(
                teacher_id=exam.teacher_id,
                class_id=exam.class_id,
                exam_id=exam.id,
                student_id=student.id,
                token=self._generate_unique_token(),
                expires_at=exam.end_time,
            )
            for student in students
            if student.id not in existing_student_ids
        ]

    def _generate_unique_token(self) -> str:
        for _ in range(10):
            token = secrets.token_urlsafe(48)
            if not self.repository.token_exists(token):
                return token
        raise exam_not_ready({"exam_tokens": ["Could not generate a unique exam token."]})

    @staticmethod
    def _build_invitation_payload(
        *,
        exam: Exam,
        student: Student,
        teacher: User,
        token: ExamToken,
    ) -> dict:
        frontend_base_url = settings.FRONTEND_BASE_URL.rstrip("/")
        return {
            "student_full_name": student.full_name,
            "exam_title": exam.title,
            "class_title": exam.classroom.title if exam.classroom is not None else "",
            "teacher_name": teacher.full_name,
            "start_time": exam.start_time.isoformat() if exam.start_time else None,
            "duration_minutes": exam.duration_minutes,
            "exam_link": f"{frontend_base_url}/exam/access/{token.token}",
        }

    def _build_blueprint(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: BlueprintCreate | BlueprintUpdate,
        teacher: User,
    ) -> ExamBlueprint:
        blueprint = ExamBlueprint(
            teacher_id=teacher.id,
            class_id=class_id,
            exam_id=exam_id,
        )
        self._apply_blueprint_counts(blueprint, payload)
        return blueprint

    @staticmethod
    def _apply_blueprint_counts(
        blueprint: ExamBlueprint,
        payload: BlueprintCreate | BlueprintUpdate,
    ) -> None:
        blueprint.multiple_choice_count = payload.multiple_choice_count
        blueprint.short_answer_count = payload.short_answer_count
        blueprint.essay_count = payload.essay_count
        blueprint.true_false_count = payload.true_false_count
        blueprint.total_question_count = (
            payload.multiple_choice_count
            + payload.short_answer_count
            + payload.essay_count
            + payload.true_false_count
        )

    @staticmethod
    def _build_question_slots(
        class_id: UUID,
        exam_id: UUID,
        teacher: User,
        payload: BlueprintCreate | BlueprintUpdate,
    ) -> list[Question]:
        slot_types = (
            [QuestionType.MULTIPLE_CHOICE.value] * payload.multiple_choice_count
            + [QuestionType.SHORT_ANSWER.value] * payload.short_answer_count
            + [QuestionType.ESSAY.value] * payload.essay_count
            + [QuestionType.TRUE_FALSE.value] * payload.true_false_count
        )
        return [
            Question(
                teacher_id=teacher.id,
                class_id=class_id,
                exam_id=exam_id,
                type=question_type,
                order_index=index,
            )
            for index, question_type in enumerate(slot_types, start=1)
        ]

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
