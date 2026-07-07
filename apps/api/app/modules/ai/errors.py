from fastapi import status

from app.core.exceptions import AppException


class AIErrorCode:
    AI_CONFIGURATION_ERROR = "AI_CONFIGURATION_ERROR"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_RESPONSE_INVALID = "AI_RESPONSE_INVALID"
    AI_TASK_NOT_SUPPORTED = "AI_TASK_NOT_SUPPORTED"


def ai_configuration_error(message: str = "AI provider is not configured correctly.") -> AppException:
    return AppException(
        code=AIErrorCode.AI_CONFIGURATION_ERROR,
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def ai_provider_error(message: str = "AI provider request failed.") -> AppException:
    return AppException(
        code=AIErrorCode.AI_PROVIDER_ERROR,
        message=message,
        status_code=status.HTTP_502_BAD_GATEWAY,
    )


def ai_response_invalid(details: dict | None = None) -> AppException:
    return AppException(
        code=AIErrorCode.AI_RESPONSE_INVALID,
        message="AI response was invalid.",
        status_code=status.HTTP_502_BAD_GATEWAY,
        details=details,
    )


def ai_task_not_supported(task_name: str) -> AppException:
    return AppException(
        code=AIErrorCode.AI_TASK_NOT_SUPPORTED,
        message=f"AI task is not supported: {task_name}.",
        status_code=status.HTTP_400_BAD_REQUEST,
    )
