from fastapi import status

from app.core.exceptions import AppException


class SubmissionErrorCode:
    SUBMISSION_NOT_FOUND = "SUBMISSION_NOT_FOUND"
    ANSWER_NOT_FOUND = "ANSWER_NOT_FOUND"


def submission_not_found() -> AppException:
    return AppException(
        code=SubmissionErrorCode.SUBMISSION_NOT_FOUND,
        message="Submission was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def answer_not_found() -> AppException:
    return AppException(
        code=SubmissionErrorCode.ANSWER_NOT_FOUND,
        message="Answer was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )

