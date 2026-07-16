from fastapi import status

from app.core.exceptions import AppException


class ExamErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    EXAM_NOT_FOUND = "EXAM_NOT_FOUND"
    EXAM_NOT_IN_CLASS = "EXAM_NOT_IN_CLASS"
    EXAM_ALREADY_HAS_BLUEPRINT = "EXAM_ALREADY_HAS_BLUEPRINT"
    EXAM_NOT_DRAFT = "EXAM_NOT_DRAFT"
    EXAM_NOT_FINALIZED = "EXAM_NOT_FINALIZED"
    EXAM_CANNOT_BE_REOPENED = "EXAM_CANNOT_BE_REOPENED"
    EXAM_ALREADY_DRAFT = "EXAM_ALREADY_DRAFT"
    EXAM_IN_PROGRESS = "EXAM_IN_PROGRESS"
    EXAM_SCHEDULE_INVALID = "EXAM_SCHEDULE_INVALID"
    EXAM_HAS_TOKENS = "EXAM_HAS_TOKENS"
    EXAM_HAS_SUBMISSIONS = "EXAM_HAS_SUBMISSIONS"
    EXAM_REQUIRES_STUDENTS = "EXAM_REQUIRES_STUDENTS"
    EXAM_TITLE_ALREADY_EXISTS = "EXAM_TITLE_ALREADY_EXISTS"
    BLUEPRINT_NOT_FOUND = "BLUEPRINT_NOT_FOUND"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    EXAM_NOT_READY = "EXAM_NOT_READY"
    EXAM_ALREADY_SCHEDULED = "EXAM_ALREADY_SCHEDULED"
    EXAM_NOT_SCHEDULED = "EXAM_NOT_SCHEDULED"
    STUDENT_NOT_IN_CLASS = "STUDENT_NOT_IN_CLASS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FORBIDDEN = "FORBIDDEN"
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"
    BLUEPRINT_UPDATE_REQUIRES_CONFIRMATION = "BLUEPRINT_UPDATE_REQUIRES_CONFIRMATION"


def class_not_found() -> AppException:
    return AppException(
        code=ExamErrorCode.CLASS_NOT_FOUND,
        message="Class was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def exam_not_found() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_NOT_FOUND,
        message="Exam was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def exam_not_in_class() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_NOT_IN_CLASS,
        message="Exam was not found in this class.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def exam_already_has_blueprint() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_ALREADY_HAS_BLUEPRINT,
        message="Exam already has a blueprint.",
        status_code=status.HTTP_409_CONFLICT,
    )


def exam_not_draft() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_NOT_DRAFT,
        message="Exam must be in draft status.",
        status_code=status.HTTP_409_CONFLICT,
    )


def exam_not_finalized(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_NOT_FINALIZED,
        message="Exam must be finalized before scheduling.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_cannot_be_reopened(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_CANNOT_BE_REOPENED,
        message="Exam cannot be reopened.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_already_draft(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_ALREADY_DRAFT,
        message="Exam is already in draft status.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_in_progress(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_IN_PROGRESS,
        message="Exam is currently in progress.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_schedule_invalid(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_SCHEDULE_INVALID,
        message="Exam schedule is invalid.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_has_tokens(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_HAS_TOKENS,
        message="Exam already has active access tokens.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_has_submissions(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_HAS_SUBMISSIONS,
        message="Exam already has active submissions.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_requires_students() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_REQUIRES_STUDENTS,
        message="Class must have at least one active student before creating an exam.",
        status_code=status.HTTP_409_CONFLICT,
    )


def exam_title_already_exists() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_TITLE_ALREADY_EXISTS,
        message="An exam with this title already exists in this class.",
        status_code=status.HTTP_409_CONFLICT,
    )


def blueprint_not_found() -> AppException:
    return AppException(
        code=ExamErrorCode.BLUEPRINT_NOT_FOUND,
        message="Blueprint was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def blueprint_update_requires_confirmation(details: dict) -> AppException:
    return AppException(
        code=ExamErrorCode.BLUEPRINT_UPDATE_REQUIRES_CONFIRMATION,
        message="Blueprint update requires explicit destructive confirmation.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def question_not_found() -> AppException:
    return AppException(
        code=ExamErrorCode.QUESTION_NOT_FOUND,
        message="Question was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def exam_not_ready(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_NOT_READY,
        message="Exam is not ready to be scheduled.",
        status_code=status.HTTP_409_CONFLICT,
        details=details,
    )


def exam_already_scheduled() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_ALREADY_SCHEDULED,
        message="Exam is already scheduled.",
        status_code=status.HTTP_409_CONFLICT,
    )


def exam_not_scheduled() -> AppException:
    return AppException(
        code=ExamErrorCode.EXAM_NOT_SCHEDULED,
        message="Exam must be scheduled before invitations can be sent.",
        status_code=status.HTTP_409_CONFLICT,
    )


def student_not_in_class() -> AppException:
    return AppException(
        code=ExamErrorCode.STUDENT_NOT_IN_CLASS,
        message="Student was not found in this class.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def validation_error(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.VALIDATION_ERROR,
        message="Request validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def email_send_failed(details: dict | None = None) -> AppException:
    return AppException(
        code=ExamErrorCode.EMAIL_SEND_FAILED,
        message="Invitation emails could not be queued.",
        status_code=status.HTTP_502_BAD_GATEWAY,
        details=details,
    )
