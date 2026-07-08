import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.infrastructure.email.providers.base import BaseEmailProvider, EmailProviderResult


class SMTPEmailProvider(BaseEmailProvider):
    async def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
        metadata: dict | None = None,
    ) -> EmailProviderResult:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            return EmailProviderResult(
                success=False,
                error_message="SMTP_HOST and SMTP_FROM_EMAIL are required for smtp email provider.",
            )

        message = EmailMessage()
        from_name = settings.SMTP_FROM_NAME.strip()
        from_header = (
            f"{from_name} <{settings.SMTP_FROM_EMAIL}>"
            if from_name
            else settings.SMTP_FROM_EMAIL
        )
        message["From"] = from_header
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body_text)
        if body_html:
            message.add_alternative(body_html, subtype="html")

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
                response = smtp.send_message(message)
        except Exception as exc:
            return EmailProviderResult(success=False, error_message=str(exc))

        return EmailProviderResult(
            success=True,
            raw_response={"provider": "smtp", "response": response},
        )

