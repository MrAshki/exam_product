import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.base import Base, BaseModelMixin


class Student(BaseModelMixin, Base):
    __tablename__ = "students"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index]:
        return (
            Index(
                "uq_students_teacher_email_active",
                "teacher_id",
                func.lower(cls.email),
                unique=True,
                postgresql_where=cls.deleted_at.is_(None),
            ),
        )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    student_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    teacher_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher = relationship("User")


class ClassStudent(BaseModelMixin, Base):
    __tablename__ = "class_students"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index]:
        return (
            Index(
                "uq_class_students_active_membership",
                "class_id",
                "student_id",
                unique=True,
                postgresql_where=cls.deleted_at.is_(None),
            ),
        )

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    classroom = relationship("Classroom")
    student = relationship("Student")
