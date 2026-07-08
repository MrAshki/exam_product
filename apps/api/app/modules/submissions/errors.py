from fastapi import status

from app.core.exceptions import AppException


class SubmissionErrorCode:
    INVALID_EXAM_TOKEN = "INVALID_EXAM_TOKEN"
    EXAM_NOT_ACTIVE = "EXAM_NOT_ACTIVE"
    EXAM_ALREADY_SUBMITTED = "EXAM_ALREADY_SUBMITTED"
    EXAM_TIME_EXPIRED = "EXAM_TIME_EXPIRED"
    SUBMISSION_NOT_FOUND = "SUBMISSION_NOT_FOUND"
    SUBMISSION_NOT_IN_PROGRESS = "SUBMISSION_NOT_IN_PROGRESS"
    ANSWER_NOT_FOUND = "ANSWER_NOT_FOUND"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    QUESTION_NOT_CONFIRMED = "QUESTION_NOT_CONFIRMED"
    VALIDATION_ERROR = "VALIDATION_ERROR"


def invalid_exam_token() -> AppException:
    return AppException(
        code=SubmissionErrorCode.INVALID_EXAM_TOKEN,
        message="Invalid exam token.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def exam_not_active() -> AppException:
    return AppException(
        code=SubmissionErrorCode.EXAM_NOT_ACTIVE,
        message="Exam is not active.",
        status_code=status.HTTP_409_CONFLICT,
    )


def exam_already_submitted() -> AppException:
    return AppException(
        code=SubmissionErrorCode.EXAM_ALREADY_SUBMITTED,
        message="Exam was already submitted.",
        status_code=status.HTTP_409_CONFLICT,
    )


def exam_time_expired() -> AppException:
    return AppException(
        code=SubmissionErrorCode.EXAM_TIME_EXPIRED,
        message="Exam time has expired.",
        status_code=status.HTTP_409_CONFLICT,
    )


def submission_not_found() -> AppException:
    return AppException(
        code=SubmissionErrorCode.SUBMISSION_NOT_FOUND,
        message="Submission was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def submission_not_in_progress() -> AppException:
    return AppException(
        code=SubmissionErrorCode.SUBMISSION_NOT_IN_PROGRESS,
        message="Submission is not in progress.",
        status_code=status.HTTP_409_CONFLICT,
    )


def answer_not_found() -> AppException:
    return AppException(
        code=SubmissionErrorCode.ANSWER_NOT_FOUND,
        message="Answer was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def question_not_found(details: dict | None = None) -> AppException:
    return AppException(
        code=SubmissionErrorCode.QUESTION_NOT_FOUND,
        message="Question was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
        details=details,
    )


def question_not_confirmed(details: dict | None = None) -> AppException:
    return AppException(
        code=SubmissionErrorCode.QUESTION_NOT_CONFIRMED,
        message="Question is not confirmed.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def validation_error(details: dict | None = None) -> AppException:
    return AppException(
        code=SubmissionErrorCode.VALIDATION_ERROR,
        message="Request validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )
