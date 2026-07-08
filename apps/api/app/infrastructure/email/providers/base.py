from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EmailProviderResult:
    success: bool
    provider_message_id: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] | str | None = None


class BaseEmailProvider:
    async def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
        metadata: dict | None = None,
    ) -> EmailProviderResult:
        raise NotImplementedError

