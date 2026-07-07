from fastapi import status

from app.core.exceptions import AppException


def job_not_found() -> AppException:
    return AppException(
        code="JOB_NOT_FOUND",
        message="Job was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def job_access_denied() -> AppException:
    return AppException(
        code="JOB_ACCESS_DENIED",
        message="You do not have access to this job.",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def job_enqueue_failed(message: str = "Job could not be enqueued.") -> AppException:
    return AppException(
        code="JOB_ENQUEUE_FAILED",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def job_update_failed(message: str = "Job could not be updated.") -> AppException:
    return AppException(
        code="JOB_UPDATE_FAILED",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

