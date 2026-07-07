from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
