from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    body_text: str
    body_html: str | None = None

