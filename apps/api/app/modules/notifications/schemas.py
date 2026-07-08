from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class EmailLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID | None
    class_id: UUID | None
    exam_id: UUID | None
    student_id: UUID | None
    email: EmailStr
    type: str
    status: str
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime

