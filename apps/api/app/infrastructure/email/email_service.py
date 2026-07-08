import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.infrastructure.email.email_logger import EmailLogger
from app.infrastructure.email.providers.base import BaseEmailProvider, EmailProviderResult
from app.infrastructure.email.providers.gmail import GmailEmailProvider
from app.infrastructure.email.providers.mock import MockEmailProvider
from app.infrastructure.email.providers.smtp import SMTPEmailProvider
from app.infrastructure.email.templates import render_email_template
from app.modules.notifications.constants import EmailStatus, VALID_EMAIL_TYPES
from app.modules.notifications.errors import email_provider_configuration_error, unsupported_email_type


@dataclass(frozen=True)
class EmailSendResult:
    success: bool
    provider_message_id: str | None
    error_message: str | None
    raw_response: dict[str, Any] | str | None


class EmailService:
    def __init__(
        self,
        db: Session,
        provider: BaseEmailProvider | None = None,
    ) -> None:
        self.db = db
        self.logger = EmailLogger(db)
        self.provider = provider or self._build_provider()

    def send_email(
        self,
        *,
        email_type: str,
        to_email: str,
        template_payload: dict[str, Any],
        subject: str | None = None,
        teacher_id: UUID | None = None,
        class_id: UUID | None = None,
        exam_id: UUID | None = None,
        student_id: UUID | None = None,
    ) -> EmailSendResult:
        if email_type not in VALID_EMAIL_TYPES:
            raise unsupported_email_type(email_type)

        rendered = render_email_template(email_type, template_payload)
        provider_result = self._send_with_provider(
            to_email=to_email,
            subject=subject or rendered.subject,
            body_text=rendered.body_text,
            body_html=rendered.body_html,
            metadata={
                "email_type": email_type,
                **template_payload,
            },
        )

        status = EmailStatus.SENT if provider_result.success else EmailStatus.FAILED
        try:
            self.logger.log_attempt(
                email=to_email,
                email_type=email_type,
                status=status,
                teacher_id=teacher_id,
                class_id=class_id,
                exam_id=exam_id,
                student_id=student_id,
                error_message=provider_result.error_message,
            )
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return EmailSendResult(
            success=provider_result.success,
            provider_message_id=provider_result.provider_message_id,
            error_message=provider_result.error_message,
            raw_response=provider_result.raw_response,
        )

    def _send_with_provider(
        self,
        *,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None,
        metadata: dict[str, Any],
    ) -> EmailProviderResult:
        return asyncio.run(
            self.provider.send(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                metadata=metadata,
            )
        )

    @staticmethod
    def _build_provider() -> BaseEmailProvider:
        provider = settings.EMAIL_PROVIDER.lower().strip()
        if provider == "mock":
            return MockEmailProvider()
        if provider == "smtp":
            return SMTPEmailProvider()
        if provider == "gmail":
            return GmailEmailProvider()
        raise email_provider_configuration_error(
            f"Unsupported EMAIL_PROVIDER: {settings.EMAIL_PROVIDER}"
        )

