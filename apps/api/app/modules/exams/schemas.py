from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExamCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    total_points: int = Field(default=0, ge=0)
    show_leaderboard: bool = True
    allow_appeals: bool = True
    show_correct_answers: bool = True
    show_feedback: bool = True

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("description")
    @classmethod
    def empty_description_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExamUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    total_points: int | None = Field(default=None, ge=0)
    show_leaderboard: bool | None = None
    allow_appeals: bool | None = None
    show_correct_answers: bool | None = None
    show_feedback: bool | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("description")
    @classmethod
    def empty_description_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExamRead(BaseModel):
    id: UUID
    teacher_id: UUID
    class_id: UUID
    title: str
    description: str | None
    start_time: datetime | None
    end_time: datetime | None
    duration_minutes: int | None
    status: str
    total_points: int
    show_leaderboard: bool
    allow_appeals: bool
    show_correct_answers: bool
    show_feedback: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamScheduleRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_minutes: int = Field(gt=0)

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start_time(cls, value: datetime, info) -> datetime:
        start_time = info.data.get("start_time")
        if start_time is not None and value <= start_time:
            raise ValueError("End time must be after start time.")
        return value


class ExamScheduleRead(BaseModel):
    id: UUID
    status: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    created_exam_tokens: int


class ExamInvitationRequest(BaseModel):
    send_to_all: bool = True


class ExamInvitationRead(BaseModel):
    queued_emails: int


class BlueprintBase(BaseModel):
    multiple_choice_count: int = Field(default=0, ge=0)
    short_answer_count: int = Field(default=0, ge=0)
    essay_count: int = Field(default=0, ge=0)
    true_false_count: int = Field(default=0, ge=0)


class BlueprintCreate(BlueprintBase):
    pass


class BlueprintUpdate(BlueprintBase):
    pass


class BlueprintRead(BlueprintBase):
    id: UUID
    teacher_id: UUID
    class_id: UUID
    exam_id: UUID
    total_question_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
