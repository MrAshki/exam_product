from fastapi import status

from app.core.exceptions import AppException
from app.modules.exams.errors import class_not_found, exam_not_draft, exam_not_found


class QuestionErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    EXAM_NOT_FOUND = "EXAM_NOT_FOUND"
    EXAM_NOT_IN_CLASS = "EXAM_NOT_IN_CLASS"
    EXAM_NOT_DRAFT = "EXAM_NOT_DRAFT"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    QUESTION_NOT_IN_EXAM = "QUESTION_NOT_IN_EXAM"
    QUESTION_VALIDATION_FAILED = "QUESTION_VALIDATION_FAILED"
    QUESTION_ALREADY_CONFIRMED = "QUESTION_ALREADY_CONFIRMED"
    QUESTION_TYPE_NOT_SUPPORTED = "QUESTION_TYPE_NOT_SUPPORTED"
    QUESTION_NOT_READY_FOR_AI = "QUESTION_NOT_READY_FOR_AI"
    INVALID_QUESTION_TYPE = "INVALID_QUESTION_TYPE"
    INVALID_QUESTION_OPTIONS = "INVALID_QUESTION_OPTIONS"


def question_not_found() -> AppException:
    return AppException(
        code=QuestionErrorCode.QUESTION_NOT_FOUND,
        message="Question was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def question_not_in_exam() -> AppException:
    return AppException(
        code=QuestionErrorCode.QUESTION_NOT_IN_EXAM,
        message="Question was not found in this exam.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def question_validation_failed(details: dict) -> AppException:
    return AppException(
        code=QuestionErrorCode.QUESTION_VALIDATION_FAILED,
        message="Question is incomplete or invalid.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def question_already_confirmed() -> AppException:
    return AppException(
        code=QuestionErrorCode.QUESTION_ALREADY_CONFIRMED,
        message="Question is already confirmed.",
        status_code=status.HTTP_409_CONFLICT,
    )


def question_type_not_supported() -> AppException:
    return AppException(
        code=QuestionErrorCode.QUESTION_TYPE_NOT_SUPPORTED,
        message="Question type is not supported for this action.",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def question_not_ready_for_ai(details: dict) -> AppException:
    return AppException(
        code=QuestionErrorCode.QUESTION_NOT_READY_FOR_AI,
        message="Question is not ready for AI assistance.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def invalid_question_type() -> AppException:
    return AppException(
        code=QuestionErrorCode.INVALID_QUESTION_TYPE,
        message="Question type is not supported.",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def invalid_question_options(details: dict) -> AppException:
    return AppException(
        code=QuestionErrorCode.INVALID_QUESTION_OPTIONS,
        message="Question options are invalid.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


__all__ = [
    "class_not_found",
    "exam_not_draft",
    "exam_not_found",
    "invalid_question_options",
    "invalid_question_type",
    "question_already_confirmed",
    "question_not_ready_for_ai",
    "question_not_found",
    "question_not_in_exam",
    "question_type_not_supported",
    "question_validation_failed",
]
