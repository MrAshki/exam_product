from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StudentBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    student_code: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    teacher_note: str | None = Field(default=None, max_length=5000)

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("student_code", "teacher_note")
    @classmethod
    def empty_optional_text_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    student_code: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    teacher_note: str | None = Field(default=None, max_length=5000)

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("student_code", "teacher_note")
    @classmethod
    def empty_optional_text_becomes_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class StudentRead(BaseModel):
    id: UUID
    teacher_id: UUID
    full_name: str
    email: EmailStr
    student_code: str | None
    is_active: bool
    teacher_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentList(BaseModel):
    items: list[StudentRead]
    page: int
    page_size: int
    total: int
