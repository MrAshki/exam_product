from enum import StrEnum


class ExamStatus(StrEnum):
    DRAFT = "draft"


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    TRUE_FALSE = "true_false"


class QuestionStatus(StrEnum):
    EMPTY = "empty"


class QuestionSourceType(StrEnum):
    TYPED = "typed"


class ExtractionMode(StrEnum):
    NONE = "none"
