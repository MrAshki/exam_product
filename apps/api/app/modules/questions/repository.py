from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.questions.models import Question


class QuestionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_class_for_teacher(
        self,
        class_id: UUID,
        teacher_id: UUID,
    ) -> Classroom | None:
        statement = select(Classroom).where(
            Classroom.id == class_id,
            Classroom.teacher_id == teacher_id,
            Classroom.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def get_exam_for_teacher_class(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> Exam | None:
        statement = select(Exam).where(
            Exam.id == exam_id,
            Exam.class_id == class_id,
            Exam.teacher_id == teacher_id,
            Exam.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def list_slots_for_exam(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> list[Question]:
        statement = (
            select(Question)
            .where(
                Question.exam_id == exam_id,
                Question.class_id == class_id,
                Question.teacher_id == teacher_id,
                Question.deleted_at.is_(None),
            )
            .order_by(Question.order_index.asc())
        )
        return list(self.db.scalars(statement).all())
