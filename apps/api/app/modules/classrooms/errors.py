from fastapi import status

from app.core.exceptions import AppException


class ClassroomErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    CLASS_TITLE_ALREADY_EXISTS = "CLASS_TITLE_ALREADY_EXISTS"


def class_not_found() -> AppException:
    return AppException(
        code=ClassroomErrorCode.CLASS_NOT_FOUND,
        message="Class was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def class_title_already_exists() -> AppException:
    return AppException(
        code=ClassroomErrorCode.CLASS_TITLE_ALREADY_EXISTS,
        message="A class with this title already exists.",
        status_code=status.HTTP_409_CONFLICT,
    )
