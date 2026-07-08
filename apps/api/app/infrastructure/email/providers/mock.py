from app.infrastructure.email.providers.base import BaseEmailProvider, EmailProviderResult


class MockEmailProvider(BaseEmailProvider):
    async def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
        metadata: dict | None = None,
    ) -> EmailProviderResult:
        metadata = metadata or {}
        if metadata.get("force_fail") or metadata.get("force_failure"):
            return EmailProviderResult(
                success=False,
                error_message="Forced mock email failure.",
                raw_response={"provider": "mock", "forced_failure": True},
            )

        return EmailProviderResult(
            success=True,
            provider_message_id=f"mock-{to_email}-{subject}".lower().replace(" ", "-"),
            raw_response={"provider": "mock", "delivered": True},
        )

