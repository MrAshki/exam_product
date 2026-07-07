from fastapi import status

from app.core.exceptions import AppException


class AuthErrorCode:
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    INACTIVE_USER = "INACTIVE_USER"


def email_already_registered() -> AppException:
    return AppException(
        code=AuthErrorCode.EMAIL_ALREADY_REGISTERED,
        message="A user with this email already exists.",
        status_code=status.HTTP_409_CONFLICT,
    )


def invalid_credentials() -> AppException:
    return AppException(
        code=AuthErrorCode.INVALID_CREDENTIALS,
        message="Invalid email or password.",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def not_authenticated() -> AppException:
    return AppException(
        code=AuthErrorCode.NOT_AUTHENTICATED,
        message="Authentication is required.",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def inactive_user() -> AppException:
    return AppException(
        code=AuthErrorCode.INACTIVE_USER,
        message="User account is inactive.",
        status_code=status.HTTP_403_FORBIDDEN,
    )
