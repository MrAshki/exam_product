from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom
from app.modules.students.models import ClassStudent, Student


class StudentRepository:
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

    def get_student_by_email_for_teacher(
        self,
        email: str,
        teacher_id: UUID,
        exclude_student_id: UUID | None = None,
    ) -> Student | None:
        statement = select(Student).where(
            Student.teacher_id == teacher_id,
            Student.deleted_at.is_(None),
            func.lower(Student.email) == email.lower(),
        )
        if exclude_student_id is not None:
            statement = statement.where(Student.id != exclude_student_id)
        return self.db.scalar(statement)

    def get_student_by_id_for_teacher(
        self,
        student_id: UUID,
        teacher_id: UUID,
    ) -> Student | None:
        statement = select(Student).where(
            Student.id == student_id,
            Student.teacher_id == teacher_id,
            Student.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def get_membership(
        self,
        class_id: UUID,
        student_id: UUID,
        include_deleted: bool = False,
    ) -> ClassStudent | None:
        statement = select(ClassStudent).where(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == student_id,
        )
        if not include_deleted:
            statement = statement.where(ClassStudent.deleted_at.is_(None))
        statement = statement.order_by(ClassStudent.created_at.desc())
        return self.db.scalar(statement)

    def list_students_for_class(
        self,
        class_id: UUID,
        teacher_id: UUID,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[Student], int]:
        filters = [
            ClassStudent.class_id == class_id,
            ClassStudent.deleted_at.is_(None),
            Student.teacher_id == teacher_id,
            Student.deleted_at.is_(None),
        ]
        if search:
            search_pattern = f"%{search.lower()}%"
            filters.append(
                or_(
                    func.lower(Student.full_name).like(search_pattern),
                    func.lower(Student.email).like(search_pattern),
                    func.lower(Student.student_code).like(search_pattern),
                )
            )

        base_statement = (
            select(Student)
            .join(ClassStudent, ClassStudent.student_id == Student.id)
            .where(*filters)
        )
        total_statement = select(func.count()).select_from(base_statement.subquery())
        total = self.db.scalar(total_statement) or 0

        statement = (
            base_statement.order_by(Student.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(statement).all()), total

    def create_student(
        self,
        teacher_id: UUID,
        full_name: str,
        email: str,
        student_code: str | None,
        is_active: bool,
        teacher_note: str | None,
    ) -> Student:
        student = Student(
            teacher_id=teacher_id,
            full_name=full_name,
            email=email,
            student_code=student_code,
            is_active=is_active,
            teacher_note=teacher_note,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def create_membership(self, class_id: UUID, student_id: UUID) -> ClassStudent:
        membership = ClassStudent(class_id=class_id, student_id=student_id)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def save_student(self, student: Student) -> Student:
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def save_membership(self, membership: ClassStudent) -> ClassStudent:
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def rollback(self) -> None:
        self.db.rollback()
