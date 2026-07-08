from fastapi import status

from app.core.exceptions import AppException


class GradingErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    EXAM_NOT_FOUND = "EXAM_NOT_FOUND"
    ANSWER_NOT_FOUND = "ANSWER_NOT_FOUND"
    ANSWER_NOT_IN_EXAM = "ANSWER_NOT_IN_EXAM"
    INVALID_SCORE = "INVALID_SCORE"
    EXAM_NOT_REVIEWABLE = "EXAM_NOT_REVIEWABLE"
    GRADE_CHANGE_LOG_FAILED = "GRADE_CHANGE_LOG_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"


def class_not_found() -> AppException:
    return AppException(
        code=GradingErrorCode.CLASS_NOT_FOUND,
        message="Class was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def exam_not_found() -> AppException:
    return AppException(
        code=GradingErrorCode.EXAM_NOT_FOUND,
        message="Exam was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def answer_not_found() -> AppException:
    return AppException(
        code=GradingErrorCode.ANSWER_NOT_FOUND,
        message="Answer was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def answer_not_in_exam() -> AppException:
    return AppException(
        code=GradingErrorCode.ANSWER_NOT_IN_EXAM,
        message="Answer was not found in this exam.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def invalid_score(details: dict | None = None) -> AppException:
    return AppException(
        code=GradingErrorCode.INVALID_SCORE,
        message="Score is invalid.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def exam_not_reviewable(details: dict | None = None) -> AppException:
    return AppException(
        code=GradingErrorCode.EXAM_NOT_REVIEWABLE,
        message="Exam is not reviewable.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def grade_change_log_failed() -> AppException:
    return AppException(
        code=GradingErrorCode.GRADE_CHANGE_LOG_FAILED,
        message="Grade change log could not be created.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
