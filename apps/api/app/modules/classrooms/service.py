from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.classrooms.errors import class_not_found, class_title_already_exists
from app.modules.classrooms.models import Classroom
from app.modules.classrooms.repository import ClassroomRepository
from app.modules.classrooms.schemas import ClassroomCreate, ClassroomUpdate


class ClassroomService:
    def __init__(self, db: Session) -> None:
        self.repository = ClassroomRepository(db)

    def create(self, payload: ClassroomCreate, teacher: User) -> Classroom:
        title = payload.title.strip()
        if self.repository.get_by_title_for_teacher(title, teacher.id):
            raise class_title_already_exists()

        try:
            return self.repository.create(
                teacher_id=teacher.id,
                title=title,
                subject=payload.subject.strip(),
                description=self._clean_optional(payload.description),
                academic_year=self._clean_optional(payload.academic_year),
                grade_level=self._clean_optional(payload.grade_level),
            )
        except IntegrityError:
            self.repository.rollback()
            raise class_title_already_exists() from None

    def list(self, teacher: User) -> list[Classroom]:
        return self.repository.list_by_teacher(teacher.id)

    def get(self, class_id: UUID, teacher: User) -> Classroom:
        classroom = self.repository.get_by_id_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()
        return classroom

    def update(
        self,
        class_id: UUID,
        payload: ClassroomUpdate,
        teacher: User,
    ) -> Classroom:
        classroom = self.get(class_id, teacher)
        update_data = payload.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"] is not None:
            title = update_data["title"].strip()
            if self.repository.get_by_title_for_teacher(title, teacher.id, classroom.id):
                raise class_title_already_exists()
            classroom.title = title

        if "subject" in update_data and update_data["subject"] is not None:
            classroom.subject = update_data["subject"].strip()

        if "description" in update_data:
            classroom.description = self._clean_optional(update_data["description"])
        if "academic_year" in update_data:
            classroom.academic_year = self._clean_optional(update_data["academic_year"])
        if "grade_level" in update_data:
            classroom.grade_level = self._clean_optional(update_data["grade_level"])

        try:
            return self.repository.save(classroom)
        except IntegrityError:
            self.repository.rollback()
            raise class_title_already_exists() from None

    def delete(self, class_id: UUID, teacher: User) -> None:
        classroom = self.get(class_id, teacher)
        classroom.soft_delete()
        self.repository.save(classroom)

    def onboarding_state(self, class_id: UUID, teacher: User) -> dict:
        classroom = self.get(class_id, teacher)
        return {
            "class_id": classroom.id,
            "class_created": True,
            "profile_complete": bool(
                classroom.title
                and classroom.subject
                and classroom.academic_year
                and classroom.grade_level
            ),
            "has_description": bool(classroom.description),
            "has_academic_year": bool(classroom.academic_year),
            "has_grade_level": bool(classroom.grade_level),
        }

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
