from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.notifications.constants import EmailStatus
from app.modules.notifications.models import EmailLog
from app.modules.notifications.repository import EmailLogRepository


class EmailLogger:
    def __init__(self, db: Session) -> None:
        self.repository = EmailLogRepository(db)

    def log_attempt(
        self,
        *,
        email: str,
        email_type: str,
        status: EmailStatus,
        teacher_id: UUID | None = None,
        class_id: UUID | None = None,
        exam_id: UUID | None = None,
        student_id: UUID | None = None,
        error_message: str | None = None,
    ) -> EmailLog:
        email_log = EmailLog(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            email=email,
            type=email_type,
            status=status.value,
            error_message=error_message,
            sent_at=datetime.now(timezone.utc) if status == EmailStatus.SENT else None,
        )
        return self.repository.create(email_log)

