from fastapi import status

from app.core.exceptions import AppException


class AppealErrorCode:
    INVALID_RESULT_TOKEN = "INVALID_RESULT_TOKEN"
    RESULT_NOT_PUBLISHED = "RESULT_NOT_PUBLISHED"
    APPEALS_NOT_ALLOWED = "APPEALS_NOT_ALLOWED"
    ANSWER_NOT_FOUND = "ANSWER_NOT_FOUND"
    ANSWER_NOT_IN_SUBMISSION = "ANSWER_NOT_IN_SUBMISSION"
    APPEAL_NOT_FOUND = "APPEAL_NOT_FOUND"
    APPEAL_ALREADY_EXISTS = "APPEAL_ALREADY_EXISTS"
    APPEAL_ALREADY_RESOLVED = "APPEAL_ALREADY_RESOLVED"
    INVALID_APPEAL_STATUS = "INVALID_APPEAL_STATUS"
    INVALID_SCORE = "INVALID_SCORE"
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    JOB_ENQUEUE_FAILED = "JOB_ENQUEUE_FAILED"


def invalid_result_token() -> AppException:
    return AppException(AppealErrorCode.INVALID_RESULT_TOKEN, "Result token is invalid.", status.HTTP_404_NOT_FOUND)


def result_not_published() -> AppException:
    return AppException(AppealErrorCode.RESULT_NOT_PUBLISHED, "Result is not published.", status.HTTP_404_NOT_FOUND)


def appeals_not_allowed() -> AppException:
    return AppException(AppealErrorCode.APPEALS_NOT_ALLOWED, "Appeals are not allowed for this exam.", status.HTTP_409_CONFLICT)


def answer_not_found() -> AppException:
    return AppException(AppealErrorCode.ANSWER_NOT_FOUND, "Answer was not found.", status.HTTP_404_NOT_FOUND)


def answer_not_in_submission() -> AppException:
    return AppException(
        AppealErrorCode.ANSWER_NOT_IN_SUBMISSION,
        "Answer was not found in this submission.",
        status.HTTP_404_NOT_FOUND,
    )


def appeal_not_found() -> AppException:
    return AppException(AppealErrorCode.APPEAL_NOT_FOUND, "Appeal was not found.", status.HTTP_404_NOT_FOUND)


def appeal_already_exists() -> AppException:
    return AppException(
        AppealErrorCode.APPEAL_ALREADY_EXISTS,
        "A pending appeal already exists for this result.",
        status.HTTP_409_CONFLICT,
    )


def appeal_already_resolved() -> AppException:
    return AppException(
        AppealErrorCode.APPEAL_ALREADY_RESOLVED,
        "Appeal has already been resolved.",
        status.HTTP_409_CONFLICT,
    )


def invalid_appeal_status(details: dict | None = None) -> AppException:
    return AppException(
        AppealErrorCode.INVALID_APPEAL_STATUS,
        "Appeal status is invalid.",
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def invalid_score(details: dict | None = None) -> AppException:
    return AppException(
        AppealErrorCode.INVALID_SCORE,
        "Score is invalid.",
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def class_not_found() -> AppException:
    return AppException(AppealErrorCode.CLASS_NOT_FOUND, "Class was not found.", status.HTTP_404_NOT_FOUND)


def forbidden() -> AppException:
    return AppException(AppealErrorCode.FORBIDDEN, "You do not have access to this resource.", status.HTTP_403_FORBIDDEN)


def validation_error(details: dict | None = None) -> AppException:
    return AppException(
        AppealErrorCode.VALIDATION_ERROR,
        "Validation error.",
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def job_enqueue_failed(details: dict | None = None) -> AppException:
    return AppException(
        AppealErrorCode.JOB_ENQUEUE_FAILED,
        "Appeal jobs could not be queued.",
        status.HTTP_502_BAD_GATEWAY,
        details=details,
    )
