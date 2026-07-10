from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID | None
    class_id: UUID | None
    exam_id: UUID | None
    question_id: UUID | None
    submission_id: UUID | None
    job_type: str
    queue_name: str
    status: str
    entity_type: str | None
    entity_id: UUID | None
    payload_json: dict | list | None
    result_json: dict | list | None
    error_code: str | None
    error_message: str | None
    attempts: int
    max_attempts: int | None
    celery_task_id: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
