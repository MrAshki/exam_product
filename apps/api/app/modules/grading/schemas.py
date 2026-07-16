from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnswerReviewRequest(BaseModel):
    teacher_score: Decimal = Field(ge=0)
    teacher_feedback: str | None = Field(default=None, max_length=10000)
    reason: str | None = Field(default=None, max_length=10000)

    @field_validator("teacher_feedback", "reason")
    @classmethod
    def empty_string_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class AnswerReviewRead(BaseModel):
    answer_id: UUID
    submission_id: UUID
    teacher_score: Decimal
    teacher_feedback: str | None
    final_score: Decimal
    reviewed_by_teacher: bool
    needs_review: bool
    submission_total_score: Decimal
    submission_max_score: Decimal
    submission_needs_review_count: int


class ApproveResultsRead(BaseModel):
    exam_id: UUID
    status: str
    approved_submissions: int
