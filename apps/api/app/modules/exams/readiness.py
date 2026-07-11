from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from uuid import UUID

from app.modules.exams.models import Exam, ExamBlueprint
from app.modules.exams.status import ExamStatus, QuestionType
from app.modules.questions.models import Question, QuestionOption


MULTIPLE_CHOICE_KEYS = {"A", "B", "C", "D"}


class ReadinessFailureCode:
    BLUEPRINT_MISSING = "BLUEPRINT_MISSING"
    BLUEPRINT_COUNT_MISMATCH = "BLUEPRINT_COUNT_MISMATCH"
    BLUEPRINT_TYPE_MISMATCH = "BLUEPRINT_TYPE_MISMATCH"
    QUESTION_EMPTY = "QUESTION_EMPTY"
    QUESTION_TEXT_REQUIRED = "QUESTION_TEXT_REQUIRED"
    QUESTION_POINTS_INVALID = "QUESTION_POINTS_INVALID"
    INVALID_CORRECT_OPTION = "INVALID_CORRECT_OPTION"
    INVALID_QUESTION_OPTIONS = "INVALID_QUESTION_OPTIONS"
    EXPECTED_ANSWER_REQUIRED = "EXPECTED_ANSWER_REQUIRED"
    RUBRIC_REQUIRED = "RUBRIC_REQUIRED"
    RUBRIC_NOT_CONFIRMED = "RUBRIC_NOT_CONFIRMED"
    QUESTION_NEEDS_REVIEW = "QUESTION_NEEDS_REVIEW"
    POINTS_TOTAL_MISMATCH = "POINTS_TOTAL_MISMATCH"
    EXAM_NOT_DRAFT = "EXAM_NOT_DRAFT"


class ExamReadinessValidator:
    def validate(
        self,
        *,
        exam: Exam,
        blueprint: ExamBlueprint | None,
        questions: list[Question],
        options: list[QuestionOption],
    ) -> dict:
        failures: list[dict] = []
        options_by_question_id = self._options_by_question_id(options)

        if blueprint is None:
            failures.append(
                self._exam_failure(
                    ReadinessFailureCode.BLUEPRINT_MISSING,
                    "blueprint",
                    "ساختار آزمون هنوز ساخته نشده است.",
                )
            )
        else:
            failures.extend(self._validate_blueprint(blueprint, questions))

        if not questions:
            failures.append(
                self._exam_failure(
                    ReadinessFailureCode.QUESTION_EMPTY,
                    "questions",
                    "هیچ جایگاه سوال فعالی برای این آزمون وجود ندارد.",
                )
            )

        for question in questions:
            failures.extend(self._validate_question(question, options_by_question_id.get(question.id, [])))

        calculated_points = sum((Decimal(question.points) for question in questions), Decimal("0"))
        exam_total_points = Decimal(exam.total_points)
        if calculated_points != exam_total_points:
            failures.append(
                self._exam_failure(
                    ReadinessFailureCode.POINTS_TOTAL_MISMATCH,
                    "total_points",
                    f"مجموع نمره سوال‌ها ({self._format_decimal(calculated_points)}) باید با نمره آزمون ({self._format_decimal(exam_total_points)}) برابر باشد.",
                )
            )

        question_ids_with_failures = {
            failure["question_id"]
            for failure in failures
            if failure.get("question_id") is not None
        }
        complete_question_count = max(len(questions) - len(question_ids_with_failures), 0)
        blueprint_match = blueprint is not None and not any(
            failure["code"]
            in {
                ReadinessFailureCode.BLUEPRINT_COUNT_MISMATCH,
                ReadinessFailureCode.BLUEPRINT_TYPE_MISMATCH,
            }
            for failure in failures
        )
        points_match = calculated_points == exam_total_points
        is_ready = not failures

        return {
            "exam_id": exam.id,
            "exam_status": exam.status,
            "is_ready": is_ready,
            "finalization_allowed": exam.status == ExamStatus.DRAFT.value and is_ready,
            "scheduling_allowed": exam.status == ExamStatus.FINALIZED.value and is_ready,
            "total_question_count": len(questions),
            "complete_question_count": complete_question_count,
            "incomplete_question_count": len(questions) - complete_question_count,
            "calculated_question_points": calculated_points,
            "exam_total_points": exam_total_points,
            "points_match": points_match,
            "blueprint_match": blueprint_match,
            "failures": failures,
        }

    def _validate_blueprint(
        self,
        blueprint: ExamBlueprint,
        questions: list[Question],
    ) -> list[dict]:
        failures: list[dict] = []
        if len(questions) != blueprint.total_question_count:
            failures.append(
                self._exam_failure(
                    ReadinessFailureCode.BLUEPRINT_COUNT_MISMATCH,
                    "questions",
                    "تعداد سوال‌های فعال با ساختار آزمون برابر نیست.",
                )
            )

        actual_counts = Counter(question.type for question in questions)
        expected_counts = {
            QuestionType.MULTIPLE_CHOICE.value: blueprint.multiple_choice_count,
            QuestionType.SHORT_ANSWER.value: blueprint.short_answer_count,
            QuestionType.ESSAY.value: blueprint.essay_count,
            QuestionType.TRUE_FALSE.value: blueprint.true_false_count,
        }
        for question_type, expected_count in expected_counts.items():
            if actual_counts.get(question_type, 0) != expected_count:
                failures.append(
                    self._exam_failure(
                        ReadinessFailureCode.BLUEPRINT_TYPE_MISMATCH,
                        question_type,
                        "تعداد نوع سوال‌ها با ساختار آزمون همخوان نیست.",
                    )
                )
        return failures

    def _validate_question(self, question: Question, options: list[QuestionOption]) -> list[dict]:
        failures: list[dict] = []
        if not self._has_text(question.text):
            failures.append(self._question_failure(question, ReadinessFailureCode.QUESTION_TEXT_REQUIRED, "text", "متن سوال الزامی است."))
        if Decimal(question.points) <= Decimal("0"):
            failures.append(self._question_failure(question, ReadinessFailureCode.QUESTION_POINTS_INVALID, "points", "نمره سوال باید بزرگ‌تر از صفر باشد."))
        if question.needs_teacher_review:
            failures.append(self._question_failure(question, ReadinessFailureCode.QUESTION_NEEDS_REVIEW, "needs_teacher_review", "این سوال هنوز نیاز به بازبینی معلم دارد."))

        if question.type == QuestionType.MULTIPLE_CHOICE.value:
            failures.extend(self._validate_multiple_choice(question, options))
        elif question.type == QuestionType.TRUE_FALSE.value:
            if (question.correct_answer or "").strip().lower() not in {"true", "false"}:
                failures.append(self._question_failure(question, ReadinessFailureCode.INVALID_CORRECT_OPTION, "correct_answer", "پاسخ درست باید true یا false باشد."))
        elif question.type == QuestionType.SHORT_ANSWER.value:
            if not self._has_text(question.expected_answer):
                failures.append(self._question_failure(question, ReadinessFailureCode.EXPECTED_ANSWER_REQUIRED, "expected_answer", "پاسخ مورد انتظار الزامی است."))
        elif question.type == QuestionType.ESSAY.value:
            if not self._has_text(question.expected_answer):
                failures.append(self._question_failure(question, ReadinessFailureCode.EXPECTED_ANSWER_REQUIRED, "expected_answer", "پاسخ مورد انتظار الزامی است."))
            if not question.rubric:
                failures.append(self._question_failure(question, ReadinessFailureCode.RUBRIC_REQUIRED, "rubric", "روبرک سوال تشریحی الزامی است."))
            if not question.rubric_teacher_confirmed:
                failures.append(self._question_failure(question, ReadinessFailureCode.RUBRIC_NOT_CONFIRMED, "rubric_teacher_confirmed", "روبرک باید توسط معلم تایید شود."))
        else:
            failures.append(self._question_failure(question, ReadinessFailureCode.QUESTION_EMPTY, "type", "نوع سوال پشتیبانی نمی‌شود."))
        return failures

    def _validate_multiple_choice(self, question: Question, options: list[QuestionOption]) -> list[dict]:
        failures: list[dict] = []
        normalized_keys = [self._normalize_key(option.option_key) for option in options]
        option_texts_valid = all(self._has_text(option.option_text) for option in options)
        keys_valid = set(normalized_keys) == MULTIPLE_CHOICE_KEYS and len(normalized_keys) == 4

        if len(options) != 4 or None in normalized_keys or len(set(normalized_keys)) != 4 or not option_texts_valid:
            failures.append(self._question_failure(question, ReadinessFailureCode.INVALID_QUESTION_OPTIONS, "options", "سوال تستی باید دقیقا چهار گزینه A، B، C و D با متن معتبر داشته باشد."))

        correct_answer = self._normalize_key(question.correct_answer)
        correct_options = [option for option in options if option.is_correct]
        if (
            correct_answer is None
            or not keys_valid
            or len(correct_options) != 1
            or self._normalize_key(correct_options[0].option_key) != correct_answer
        ):
            failures.append(self._question_failure(question, ReadinessFailureCode.INVALID_CORRECT_OPTION, "correct_answer", "پاسخ درست سوال تستی باید یکی از گزینه‌های A، B، C یا D و با گزینه صحیح هماهنگ باشد."))
        return failures

    @staticmethod
    def _options_by_question_id(options: list[QuestionOption]) -> dict[UUID, list[QuestionOption]]:
        grouped: dict[UUID, list[QuestionOption]] = defaultdict(list)
        for option in options:
            grouped[option.question_id].append(option)
        return grouped

    @staticmethod
    def _normalize_key(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized if normalized in MULTIPLE_CHOICE_KEYS else None

    @staticmethod
    def _has_text(value: str | None) -> bool:
        return bool(value and value.strip())

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        normalized = value.quantize(Decimal("0.01"))
        return format(normalized.normalize(), "f")

    @staticmethod
    def _exam_failure(code: str, field: str, message: str) -> dict:
        return {
            "question_id": None,
            "order_index": None,
            "question_type": None,
            "code": code,
            "field": field,
            "message": message,
        }

    @staticmethod
    def _question_failure(question: Question, code: str, field: str, message: str) -> dict:
        return {
            "question_id": question.id,
            "order_index": question.order_index,
            "question_type": question.type,
            "code": code,
            "field": field,
            "message": message,
        }
