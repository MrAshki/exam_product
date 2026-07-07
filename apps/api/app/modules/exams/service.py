from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.exams.errors import (
    blueprint_not_found,
    class_not_found,
    exam_already_has_blueprint,
    exam_not_draft,
    exam_not_found,
    exam_requires_students,
    exam_title_already_exists,
)
from app.modules.exams.models import Exam, ExamBlueprint
from app.modules.exams.repository import ExamRepository
from app.modules.exams.schemas import BlueprintCreate, BlueprintUpdate, ExamCreate, ExamUpdate
from app.modules.exams.status import ExamStatus, QuestionType
from app.modules.questions.models import Question


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
