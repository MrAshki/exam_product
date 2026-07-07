from fastapi import status

from app.core.exceptions import AppException


class StudentErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    STUDENT_NOT_FOUND = "STUDENT_NOT_FOUND"
    STUDENT_NOT_IN_CLASS = "STUDENT_NOT_IN_CLASS"
    STUDENT_ALREADY_IN_CLASS = "STUDENT_ALREADY_IN_CLASS"
    STUDENT_EMAIL_ALREADY_EXISTS = "STUDENT_EMAIL_ALREADY_EXISTS"


def class_not_found() -> AppException:
    return AppException(
        code=StudentErrorCode.CLASS_NOT_FOUND,
        message="Class was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def student_not_found() -> AppException:
    return AppException(
        code=StudentErrorCode.STUDENT_NOT_FOUND,
        message="Student was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def student_not_in_class() -> AppException:
    return AppException(
        code=StudentErrorCode.STUDENT_NOT_IN_CLASS,
        message="Student was not found in this class.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def student_already_in_class() -> AppException:
    return AppException(
        code=StudentErrorCode.STUDENT_ALREADY_IN_CLASS,
        message="Student is already in this class.",
        status_code=status.HTTP_409_CONFLICT,
    )


def student_email_already_exists() -> AppException:
    return AppException(
        code=StudentErrorCode.STUDENT_EMAIL_ALREADY_EXISTS,
        message="A student with this email already exists.",
        status_code=status.HTTP_409_CONFLICT,
    )
