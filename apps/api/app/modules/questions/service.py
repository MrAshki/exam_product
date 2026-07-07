from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.ai.schemas import AICallContext
from app.modules.ai.service import AIService
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.questions.errors import (
    class_not_found,
    exam_not_draft,
    exam_not_found,
    invalid_question_options,
    invalid_question_type,
    question_already_confirmed,
    question_not_ready_for_ai,
    question_not_found,
    question_type_not_supported,
    question_validation_failed,
)
from app.modules.questions.models import Question, QuestionOption
from app.modules.questions.repository import QuestionRepository
from app.modules.questions.schemas import QuestionOptionWrite, QuestionUpdate


class QuestionService:
    def __init__(self, db: Session) -> None:
        self.repository = QuestionRepository(db)

    def list_slots(
        self,
        class_id: UUID,
        exam_id: UUID,
        teacher: User,
    ) -> list[Question]:
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()
        exam = self.repository.get_exam_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        return self.repository.list_slots_for_exam(exam_id, class_id, teacher.id)

    def update(
        self,
        class_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        payload: QuestionUpdate,
        teacher: User,
    ) -> Question:
        exam = self._get_exam(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        question = self._get_question(class_id, exam_id, question_id, teacher)
        self._ensure_not_confirmed(question)

        options_to_replace: list[QuestionOption] | None = None
        if question.type == QuestionType.MULTIPLE_CHOICE.value:
            if payload.options is not None:
                options_to_replace = self._build_multiple_choice_options(question, payload)
            self._apply_common_fields(question, payload)
            self._validate_multiple_choice_answer_matches_options(
                question,
                options_to_replace
                if options_to_replace is not None
                else self.repository.list_options_for_question(
                    question_id=question.id,
                    exam_id=question.exam_id,
                    class_id=question.class_id,
                    teacher_id=question.teacher_id,
                ),
            )
        elif question.type == QuestionType.SHORT_ANSWER.value:
            self._apply_common_fields(question, payload)
            self.repository.clear_options(question)
        elif question.type == QuestionType.ESSAY.value:
            self._apply_common_fields(question, payload)
            if payload.rubric is not None:
                question.rubric = payload.rubric
            if payload.rubric_teacher_confirmed is not None:
                question.rubric_teacher_confirmed = payload.rubric_teacher_confirmed
            self.repository.clear_options(question)
        elif question.type == QuestionType.TRUE_FALSE.value:
            self._apply_common_fields(question, payload)
            self._normalize_true_false(question)
            self.repository.clear_options(question)
        else:
            raise invalid_question_type()

        question.status = QuestionStatus.DRAFT.value
        question.teacher_confirmed = False
        question.needs_teacher_review = False

        try:
            if question.type == QuestionType.MULTIPLE_CHOICE.value and payload.options is not None:
                return self.repository.save_question_with_options(question, options_to_replace)
            return self.repository.save_question(question)
        except IntegrityError:
            self.repository.rollback()
            raise invalid_question_options({"options": ["Option keys must be unique."]}) from None

    def confirm(
        self,
        class_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        teacher: User,
    ) -> Question:
        exam = self._get_exam(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        question = self._get_question(class_id, exam_id, question_id, teacher)
        self._ensure_not_confirmed(question)
        options = self.repository.list_options_for_question(
            question_id=question.id,
            exam_id=exam_id,
            class_id=class_id,
            teacher_id=teacher.id,
        )
        self._validate_for_confirmation(question, options)

        question.status = QuestionStatus.CONFIRMED.value
        question.teacher_confirmed = True
        question.needs_teacher_review = False
        return self.repository.save_question(question)

    def clear(
        self,
        class_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        teacher: User,
    ) -> Question:
        exam = self._get_exam(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        question = self._get_question(class_id, exam_id, question_id, teacher)
        self._ensure_not_confirmed(question)

        question.text = None
        question.correct_answer = None
        question.correct_answer_data = None
        question.expected_answer = None
        question.points = 0
        question.grading_instructions = None
        question.rubric = None
        question.rubric_ai_suggested = None
        question.rubric_teacher_confirmed = False
        question.teacher_confirmed = False
        question.needs_teacher_review = False
        question.status = QuestionStatus.EMPTY.value

        return self.repository.save_question_with_options(question, options=None)

    def suggest_rubric(
        self,
        class_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        teacher: User,
    ) -> dict:
        exam = self._get_exam(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        question = self._get_question(class_id, exam_id, question_id, teacher)
        if question.type != QuestionType.ESSAY.value:
            raise question_type_not_supported()
        self._ensure_not_confirmed(question)
        self._ensure_ready_for_ai(question)

        ai_service = AIService(self.repository.db)
        rubric = ai_service.suggest_essay_rubric(
            question_text=question.text or "",
            expected_answer=question.expected_answer or "",
            total_points=question.points,
            context=AICallContext(
                teacher_id=teacher.id,
                class_id=class_id,
                exam_id=exam_id,
                question_id=question.id,
            ),
        )

        question.rubric_ai_suggested = rubric
        question.needs_teacher_review = True
        saved_question = self.repository.save_question(question)
        return {
            "question_id": str(saved_question.id),
            "rubric_ai_suggested": rubric,
            "rubric_teacher_confirmed": saved_question.rubric_teacher_confirmed,
            "teacher_confirmed": saved_question.teacher_confirmed,
            "needs_teacher_review": saved_question.needs_teacher_review,
        }

    def get_options(self, question: Question) -> list[QuestionOption]:
        return self.repository.list_options_for_question(
            question_id=question.id,
            exam_id=question.exam_id,
            class_id=question.class_id,
            teacher_id=question.teacher_id,
        )

    def _get_exam(self, class_id: UUID, exam_id: UUID, teacher: User):
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()
        exam = self.repository.get_exam_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        return exam

    def _get_question(
        self,
        class_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        teacher: User,
    ) -> Question:
        question = self.repository.get_question_for_exam(
            question_id=question_id,
            exam_id=exam_id,
            class_id=class_id,
            teacher_id=teacher.id,
        )
        if question is None:
            raise question_not_found()
        return question

    @staticmethod
    def _ensure_exam_is_draft(exam) -> None:
        if exam.status != ExamStatus.DRAFT.value:
            raise exam_not_draft()

    @staticmethod
    def _ensure_not_confirmed(question: Question) -> None:
        if question.teacher_confirmed or question.status == QuestionStatus.CONFIRMED.value:
            raise question_already_confirmed()

    @staticmethod
    def _ensure_ready_for_ai(question: Question) -> None:
        errors: dict[str, list[str]] = {}
        if not question.text:
            errors.setdefault("text", []).append("Text is required.")
        if not question.expected_answer:
            errors.setdefault("expected_answer", []).append("Expected answer is required.")
        if question.points <= 0:
            errors.setdefault("points", []).append("Points must be greater than 0.")
        if errors:
            raise question_not_ready_for_ai(errors)

    def _apply_common_fields(self, question: Question, payload: QuestionUpdate) -> None:
        update_data = payload.model_dump(exclude_unset=True)
        for field_name in [
            "text",
            "points",
            "correct_answer",
            "correct_answer_data",
            "expected_answer",
            "grading_instructions",
        ]:
            if field_name in update_data:
                setattr(question, field_name, update_data[field_name])

    def _build_multiple_choice_options(
        self,
        question: Question,
        payload: QuestionUpdate,
    ) -> list[QuestionOption]:
        if payload.options is None:
            return []
        self._validate_option_payload(payload.options)
        return [
            QuestionOption(
                teacher_id=question.teacher_id,
                class_id=question.class_id,
                exam_id=question.exam_id,
                question_id=question.id,
                option_key=option.option_key.strip(),
                option_text=option.option_text.strip(),
                is_correct=option.is_correct,
            )
            for option in payload.options
        ]

    @staticmethod
    def _validate_option_payload(options: list[QuestionOptionWrite]) -> None:
        errors: dict[str, list[str]] = {}
        if len(options) < 2:
            errors.setdefault("options", []).append("Multiple choice requires at least 2 options.")
        normalized_keys = [option.option_key.strip().lower() for option in options]
        if len(normalized_keys) != len(set(normalized_keys)):
            errors.setdefault("options", []).append("Option keys must be unique.")
        correct_count = sum(1 for option in options if option.is_correct)
        if correct_count != 1:
            errors.setdefault("options", []).append("Exactly one option must be correct.")
        if errors:
            raise invalid_question_options(errors)

    @staticmethod
    def _normalize_true_false(question: Question) -> None:
        if question.correct_answer is not None:
            question.correct_answer = question.correct_answer.strip().lower()
        if question.correct_answer_data is not None and isinstance(question.correct_answer_data, dict):
            value = question.correct_answer_data.get("value")
            if isinstance(value, bool):
                question.correct_answer = "true" if value else "false"
        if question.correct_answer is not None and question.correct_answer not in {"true", "false"}:
            raise question_validation_failed(
                {"correct_answer": ["Correct answer must be true or false."]}
            )

    @staticmethod
    def _validate_multiple_choice_answer_matches_options(
        question: Question,
        options: list[QuestionOption],
    ) -> None:
        if not question.correct_answer or not options:
            return
        correct_options = [option for option in options if option.is_correct]
        if not correct_options:
            return
        correct_key = correct_options[0].option_key.strip().lower()
        if question.correct_answer.strip().lower() != correct_key:
            raise invalid_question_options(
                {"correct_answer": ["Correct answer must match the correct option key."]}
            )

    def _validate_for_confirmation(
        self,
        question: Question,
        options: list[QuestionOption],
    ) -> None:
        errors: dict[str, list[str]] = {}

        if not question.text:
            errors.setdefault("text", []).append("Text is required.")
        if question.points <= 0:
            errors.setdefault("points", []).append("Points must be greater than 0.")

        if question.type == QuestionType.MULTIPLE_CHOICE.value:
            self._validate_multiple_choice_for_confirmation(question, options, errors)
        elif question.type == QuestionType.SHORT_ANSWER.value:
            if not question.expected_answer:
                errors.setdefault("expected_answer", []).append("Expected answer is required.")
        elif question.type == QuestionType.ESSAY.value:
            if not question.expected_answer:
                errors.setdefault("expected_answer", []).append("Expected answer is required.")
            if not question.rubric:
                errors.setdefault("rubric", []).append("Rubric is required.")
            if not question.rubric_teacher_confirmed:
                errors.setdefault("rubric_teacher_confirmed", []).append("Rubric must be teacher confirmed.")
        elif question.type == QuestionType.TRUE_FALSE.value:
            if question.correct_answer not in {"true", "false"}:
                errors.setdefault("correct_answer", []).append("Correct answer must be true or false.")
        else:
            raise invalid_question_type()

        if errors:
            raise question_validation_failed(errors)

    @staticmethod
    def _validate_multiple_choice_for_confirmation(
        question: Question,
        options: list[QuestionOption],
        errors: dict[str, list[str]],
    ) -> None:
        if len(options) < 2:
            errors.setdefault("options", []).append("At least 2 options are required.")
        correct_options = [option for option in options if option.is_correct]
        if len(correct_options) != 1:
            errors.setdefault("options", []).append("Exactly one option must be correct.")
        if not question.correct_answer:
            errors.setdefault("correct_answer", []).append("Correct answer is required.")
        elif correct_options and question.correct_answer.strip().lower() != correct_options[0].option_key.strip().lower():
            errors.setdefault("correct_answer", []).append("Correct answer must match the correct option key.")
