from fastapi import status

from app.core.exceptions import AppException


class ExamErrorCode:
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    EXAM_NOT_FOUND = "EXAM_NOT_FOUND"
    EXAM_NOT_IN_CLASS = "EXAM_NOT_IN_CLASS"
    EXAM_ALREADY_HAS_BLUEPRINT = "EXAM_ALREADY_HAS_BLUEPRINT"
    EXAM_NOT_DRAFT = "EXAM_NOT_DRAFT"
    EXAM_REQUIRES_STUDENTS = "EXAM_REQUIRES_STUDENTS"
    EXAM_TITLE_ALREADY_EXISTS = "EXAM_TITLE_ALREADY_EXISTS"
    BLUEPRINT_NOT_FOUND = "BLUEPRINT_NOT_FOUND"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"


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


def question_not_found() -> AppException:
    return AppException(
        code=ExamErrorCode.QUESTION_NOT_FOUND,
        message="Question was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )
