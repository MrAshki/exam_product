from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.students.errors import (
    class_not_found,
    student_already_in_class,
    student_email_already_exists,
    student_not_found,
    student_not_in_class,
)
from app.modules.students.models import ClassStudent, Student
from app.modules.students.repository import StudentRepository
from app.modules.students.schemas import StudentCreate, StudentUpdate


class StudentService:
    def __init__(self, db: Session) -> None:
        self.repository = StudentRepository(db)

    def add_to_class(
        self,
        class_id: UUID,
        payload: StudentCreate,
        teacher: User,
    ) -> Student:
        self._ensure_class_owned(class_id, teacher)
        email = payload.email.lower()

        student = self.repository.get_student_by_email_for_teacher(email, teacher.id)
        if student is None:
            try:
                student = self.repository.create_student(
                    teacher_id=teacher.id,
                    full_name=payload.full_name.strip(),
                    email=email,
                    student_code=self._clean_optional(payload.student_code),
                    is_active=payload.is_active,
                    teacher_note=self._clean_optional(payload.teacher_note),
                )
            except IntegrityError:
                self.repository.rollback()
                student = self.repository.get_student_by_email_for_teacher(email, teacher.id)
                if student is None:
                    raise student_email_already_exists() from None

        membership = self.repository.get_membership(
            class_id=class_id,
            student_id=student.id,
            include_deleted=True,
        )
        if membership is None:
            try:
                self.repository.create_membership(class_id=class_id, student_id=student.id)
            except IntegrityError:
                self.repository.rollback()
                raise student_already_in_class() from None
        elif membership.deleted_at is not None:
            membership.deleted_at = None
            try:
                self.repository.save_membership(membership)
            except IntegrityError:
                self.repository.rollback()
                raise student_already_in_class() from None

        return student

    def list(
        self,
        class_id: UUID,
        teacher: User,
        page: int,
        page_size: int,
        search: str | None,
    ) -> tuple[list[Student], int]:
        self._ensure_class_owned(class_id, teacher)
        return self.repository.list_students_for_class(
            class_id=class_id,
            teacher_id=teacher.id,
            page=page,
            page_size=page_size,
            search=self._clean_optional(search),
        )

    def get(self, class_id: UUID, student_id: UUID, teacher: User) -> Student:
        self._ensure_class_owned(class_id, teacher)
        student = self.repository.get_student_by_id_for_teacher(student_id, teacher.id)
        if student is None:
            raise student_not_found()
        membership = self._get_active_membership(class_id, student.id)
        if membership is None:
            raise student_not_in_class()
        return student

    def update(
        self,
        class_id: UUID,
        student_id: UUID,
        payload: StudentUpdate,
        teacher: User,
    ) -> Student:
        student = self.get(class_id, student_id, teacher)
        update_data = payload.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] is not None:
            email = update_data["email"].lower()
            existing = self.repository.get_student_by_email_for_teacher(
                email=email,
                teacher_id=teacher.id,
                exclude_student_id=student.id,
            )
            if existing is not None:
                raise student_email_already_exists()
            student.email = email

        if "full_name" in update_data and update_data["full_name"] is not None:
            student.full_name = update_data["full_name"].strip()
        if "student_code" in update_data:
            student.student_code = self._clean_optional(update_data["student_code"])
        if "is_active" in update_data and update_data["is_active"] is not None:
            student.is_active = update_data["is_active"]
        if "teacher_note" in update_data:
            student.teacher_note = self._clean_optional(update_data["teacher_note"])

        try:
            return self.repository.save_student(student)
        except IntegrityError:
            self.repository.rollback()
            raise student_email_already_exists() from None

    def remove_from_class(
        self,
        class_id: UUID,
        student_id: UUID,
        teacher: User,
    ) -> None:
        self._ensure_class_owned(class_id, teacher)
        student = self.repository.get_student_by_id_for_teacher(student_id, teacher.id)
        if student is None:
            raise student_not_found()
        membership = self._get_active_membership(class_id, student.id)
        if membership is None:
            raise student_not_in_class()
        membership.soft_delete()
        self.repository.save_membership(membership)

    def _ensure_class_owned(self, class_id: UUID, teacher: User) -> None:
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()

    def _get_active_membership(
        self,
        class_id: UUID,
        student_id: UUID,
    ) -> ClassStudent | None:
        return self.repository.get_membership(
            class_id=class_id,
            student_id=student_id,
            include_deleted=False,
        )

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
