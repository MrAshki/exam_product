from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class GatewayResult:
    text: str
    provider: str
    model: str
    raw_response: str | None = None
    response_json: dict[str, Any] | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


@dataclass
class AICallContext:
    teacher_id: UUID | None = None
    class_id: UUID | None = None
    exam_id: UUID | None = None
    question_id: UUID | None = None
