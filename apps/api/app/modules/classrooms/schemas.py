from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClassroomBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subject: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    academic_year: str | None = Field(default=None, max_length=50)
    grade_level: str | None = Field(default=None, max_length=50)

    @field_validator("title", "subject")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("description", "academic_year", "grade_level")
    @classmethod
    def empty_optional_text_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    academic_year: str | None = Field(default=None, max_length=50)
    grade_level: str | None = Field(default=None, max_length=50)

    @field_validator("title", "subject")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("description", "academic_year", "grade_level")
    @classmethod
    def empty_optional_text_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ClassroomRead(ClassroomBase):
    id: UUID
    teacher_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassroomOnboardingState(BaseModel):
    class_id: UUID
    class_created: bool
    profile_complete: bool
    has_description: bool
    has_academic_year: bool
    has_grade_level: bool
