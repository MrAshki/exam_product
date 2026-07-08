from sqlalchemy.orm import Session

from app.modules.notifications.models import EmailLog


class EmailLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, email_log: EmailLog) -> EmailLog:
        self.db.add(email_log)
        self.db.commit()
        self.db.refresh(email_log)
        return email_log

    def rollback(self) -> None:
        self.db.rollback()

