from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.appeals.status import RESOLUTION_DECISIONS


class AppealCreate(BaseModel):
    answer_id: UUID | None = None
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be empty.")
        return value


class AppealResolveRequest(BaseModel):
    status: str
    new_score: Decimal | None = Field(default=None, ge=0)
    teacher_response: str = Field(min_length=1)

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in RESOLUTION_DECISIONS:
            raise ValueError("Status must be accepted or rejected.")
        return normalized

    @field_validator("teacher_response")
    @classmethod
    def response_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Teacher response must not be empty.")
        return value


class AppealSubmitRead(BaseModel):
    appeal_id: str
    status: str


class AppealListItemRead(BaseModel):
    id: str
    student_id: str
    student_full_name: str
    exam_id: str
    exam_title: str
    answer_id: str | None
    status: str
    created_at: datetime


class AppealListRead(BaseModel):
    items: list[AppealListItemRead]
    page: int
    page_size: int
    total: int


class AppealAnswerRead(BaseModel):
    answer_id: str
    question_id: str
    question_text: str | None
    question_type: str
    student_answer: str | None
    answer_data: dict | list | None
    correct_answer: str | None
    correct_answer_data: dict | list | None
    expected_answer: str | None
    current_score: str | None
    max_score: str | None
    ai_feedback: str | None
    teacher_feedback: str | None
    ai_confidence: str | None


class AppealDetailRead(BaseModel):
    id: str
    student_id: str
    student_full_name: str
    student_email: str
    exam_id: str
    exam_title: str
    submission_id: str
    answer_id: str | None
    message: str
    status: str
    teacher_response: str | None
    old_score: str | None
    new_score: str | None
    created_at: datetime
    resolved_at: datetime | None
    total_score: str | None = None
    max_score: str | None = None
    needs_review_count: int | None = None
    answer: AppealAnswerRead | None


class AppealResolveRead(BaseModel):
    appeal_id: str
    status: str
    final_decision: str
    score_changed: bool
