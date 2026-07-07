from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom


class ClassroomRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_teacher(self, teacher_id: UUID) -> list[Classroom]:
        statement = (
            select(Classroom)
            .where(
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
            .order_by(Classroom.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id_for_teacher(
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

    def get_by_title_for_teacher(
        self,
        title: str,
        teacher_id: UUID,
        exclude_class_id: UUID | None = None,
    ) -> Classroom | None:
        statement = select(Classroom).where(
            Classroom.teacher_id == teacher_id,
            Classroom.deleted_at.is_(None),
            func.lower(Classroom.title) == title.lower(),
        )
        if exclude_class_id is not None:
            statement = statement.where(Classroom.id != exclude_class_id)
        return self.db.scalar(statement)

    def create(
        self,
        teacher_id: UUID,
        title: str,
        subject: str,
        description: str | None,
        academic_year: str | None,
        grade_level: str | None,
    ) -> Classroom:
        classroom = Classroom(
            teacher_id=teacher_id,
            title=title,
            subject=subject,
            description=description,
            academic_year=academic_year,
            grade_level=grade_level,
        )
        self.db.add(classroom)
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    def save(self, classroom: Classroom) -> Classroom:
        self.db.add(classroom)
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    def rollback(self) -> None:
        self.db.rollback()
