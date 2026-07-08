from fastapi import status

from app.core.exceptions import AppException


class ResultErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    EXAM_NOT_FOUND = "EXAM_NOT_FOUND"
    EXAM_NOT_APPROVED = "EXAM_NOT_APPROVED"
    EXAM_ALREADY_PUBLISHED = "EXAM_ALREADY_PUBLISHED"
    NO_APPROVED_SUBMISSIONS = "NO_APPROVED_SUBMISSIONS"
    RESULTS_INCOMPLETE = "RESULTS_INCOMPLETE"
    RESULT_TOKEN_NOT_FOUND = "RESULT_TOKEN_NOT_FOUND"
    LEADERBOARD_TOKEN_NOT_FOUND = "LEADERBOARD_TOKEN_NOT_FOUND"
    RESULT_NOT_PUBLISHED = "RESULT_NOT_PUBLISHED"
    LEADERBOARD_NOT_AVAILABLE = "LEADERBOARD_NOT_AVAILABLE"
    INVALID_RESULT_TOKEN = "INVALID_RESULT_TOKEN"
    INVALID_LEADERBOARD_TOKEN = "INVALID_LEADERBOARD_TOKEN"
    JOB_ENQUEUE_FAILED = "JOB_ENQUEUE_FAILED"


def class_not_found() -> AppException:
    return AppException(ResultErrorCode.CLASS_NOT_FOUND, "Class was not found.", status.HTTP_404_NOT_FOUND)


def exam_not_found() -> AppException:
    return AppException(ResultErrorCode.EXAM_NOT_FOUND, "Exam was not found.", status.HTTP_404_NOT_FOUND)


def exam_not_approved(details: dict | None = None) -> AppException:
    return AppException(
        ResultErrorCode.EXAM_NOT_APPROVED,
        "Exam results must be approved before publishing.",
        status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_already_published() -> AppException:
    return AppException(
        ResultErrorCode.EXAM_ALREADY_PUBLISHED,
        "Exam results have already been published.",
        status.HTTP_409_CONFLICT,
    )


def no_approved_submissions() -> AppException:
    return AppException(
        ResultErrorCode.NO_APPROVED_SUBMISSIONS,
        "No approved submissions are available to publish.",
        status.HTTP_409_CONFLICT,
    )


def results_incomplete(details: dict | None = None) -> AppException:
    return AppException(
        ResultErrorCode.RESULTS_INCOMPLETE,
        "Results are incomplete.",
        status.HTTP_409_CONFLICT,
        details=details,
    )


def invalid_result_token() -> AppException:
    return AppException(
        ResultErrorCode.INVALID_RESULT_TOKEN,
        "Result token is invalid.",
        status.HTTP_404_NOT_FOUND,
    )


def invalid_leaderboard_token() -> AppException:
    return AppException(
        ResultErrorCode.INVALID_LEADERBOARD_TOKEN,
        "Leaderboard token is invalid.",
        status.HTTP_404_NOT_FOUND,
    )


def result_not_published() -> AppException:
    return AppException(
        ResultErrorCode.RESULT_NOT_PUBLISHED,
        "Result is not published.",
        status.HTTP_404_NOT_FOUND,
    )


def leaderboard_not_available() -> AppException:
    return AppException(
        ResultErrorCode.LEADERBOARD_NOT_AVAILABLE,
        "Leaderboard is not available.",
        status.HTTP_404_NOT_FOUND,
    )


def job_enqueue_failed(details: dict | None = None) -> AppException:
    return AppException(
        ResultErrorCode.JOB_ENQUEUE_FAILED,
        "Queued publishing jobs could not be enqueued.",
        status.HTTP_502_BAD_GATEWAY,
        details=details,
    )
