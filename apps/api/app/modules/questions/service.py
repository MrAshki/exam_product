from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.exams.errors import class_not_found, exam_not_found
from app.modules.questions.models import Question
from app.modules.questions.repository import QuestionRepository


class QuestionService:
    def __init__(self, db: Session) -> None:
        self.repository = QuestionRepository(db)

    def list_slots(
        self,
        class_id: UUID,
        exam_id: UUID,
        teacher: User,
    ) -> list[Question]:
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()
        exam = self.repository.get_exam_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        return self.repository.list_slots_for_exam(exam_id, class_id, teacher.id)
