from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class ExamAccessRead(BaseModel):
    status: str
    exam_title: str
    class_title: str
    student_full_name: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int


class StudentQuestionOptionRead(BaseModel):
    option_key: str
    option_text: str


class StudentQuestionRead(BaseModel):
    id: UUID
    order_index: int
    type: str
    text: str
    points: int
    options: list[StudentQuestionOptionRead] = Field(default_factory=list)


class ExamStartRead(BaseModel):
    submission_id: UUID
    started_at: datetime
    allowed_until: datetime
    questions: list[StudentQuestionRead]


class ExamAnswerSubmit(BaseModel):
    question_id: UUID
    student_answer: str | None = Field(default=None, max_length=20000)
    answer_data: dict | list | None = None


class ExamSubmitRequest(BaseModel):
    answers: list[ExamAnswerSubmit] = Field(default_factory=list)


class ExamSubmitRead(BaseModel):
    submission_id: UUID
    status: str
    submitted_at: datetime
    saved_answers: int
