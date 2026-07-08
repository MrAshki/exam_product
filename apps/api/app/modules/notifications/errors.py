from fastapi import status

from app.core.exceptions import AppException


def unsupported_email_type(email_type: str) -> AppException:
    return AppException(
        code="UNSUPPORTED_EMAIL_TYPE",
        message="Email type is not supported.",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"email_type": email_type},
    )


def email_provider_configuration_error(message: str) -> AppException:
    return AppException(
        code="EMAIL_PROVIDER_CONFIGURATION_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

