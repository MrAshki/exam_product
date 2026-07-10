from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionOptionWrite(BaseModel):
    option_key: str = Field(min_length=1, max_length=20)
    option_text: str = Field(min_length=1, max_length=5000)
    is_correct: bool = False

    @field_validator("option_key", "option_text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value


class QuestionOptionRead(BaseModel):
    id: UUID
    option_key: str
    option_text: str
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


class QuestionUpdate(BaseModel):
    text: str | None = Field(default=None, max_length=20000)
    points: int | None = Field(default=None, ge=0)
    correct_answer: str | None = Field(default=None, max_length=5000)
    correct_answer_data: Any | None = None
    expected_answer: str | None = Field(default=None, max_length=20000)
    grading_instructions: str | None = Field(default=None, max_length=20000)
    rubric: Any | None = None
    rubric_teacher_confirmed: bool | None = None
    options: list[QuestionOptionWrite] | None = None

    @field_validator(
        "text",
        "correct_answer",
        "expected_answer",
        "grading_instructions",
    )
    @classmethod
    def empty_text_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class QuestionSlotRead(BaseModel):
    id: UUID
    order_index: int
    type: str
    status: str
    text: str | None
    points: int
    teacher_confirmed: bool
    needs_teacher_review: bool

    model_config = ConfigDict(from_attributes=True)


class QuestionRead(QuestionSlotRead):
    class_id: UUID
    exam_id: UUID
    correct_answer: str | None
    correct_answer_data: Any | None
    expected_answer: str | None
    grading_instructions: str | None
    rubric: Any | None
    rubric_ai_suggested: Any | None
    rubric_teacher_confirmed: bool
    options: list[QuestionOptionRead] = []
