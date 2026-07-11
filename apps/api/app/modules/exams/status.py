from enum import StrEnum


class ExamStatus(StrEnum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    SCHEDULED = "scheduled"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    PUBLISHED = "published"


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    TRUE_FALSE = "true_false"


class QuestionStatus(StrEnum):
    EMPTY = "empty"
    DRAFT = "draft"
    EXTRACTED = "extracted"
    CONFIRMED = "confirmed"


class QuestionSourceType(StrEnum):
    TYPED = "typed"


class ExtractionMode(StrEnum):
    NONE = "none"
