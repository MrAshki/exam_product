from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubmissionRead(BaseModel):
    id: UUID
    teacher_id: UUID
    class_id: UUID
    exam_id: UUID
    student_id: UUID
    token_id: UUID
    started_at: datetime | None
    submitted_at: datetime | None
    status: str
    total_score: Decimal | None
    max_score: Decimal | None
    ai_confidence_avg: Decimal | None
    needs_review_count: int
    teacher_approved_at: datetime | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerRead(BaseModel):
    id: UUID
    teacher_id: UUID
    class_id: UUID
    exam_id: UUID
    student_id: UUID
    submission_id: UUID
    question_id: UUID
    student_answer: str | None
    answer_data: dict | list | None
    auto_score: Decimal | None
    teacher_score: Decimal | None
    final_score: Decimal | None
    max_score: Decimal | None
    ai_feedback: str | None
    ai_confidence: Decimal | None
    needs_review: bool
    reviewed_by_teacher: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

