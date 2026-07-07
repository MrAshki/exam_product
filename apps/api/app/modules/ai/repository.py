from sqlalchemy.orm import Session

from app.modules.ai.logs import AILog


class AIRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_log(self, log: AILog) -> AILog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def rollback(self) -> None:
        self.db.rollback()
