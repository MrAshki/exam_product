import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.base import Base, BaseModelMixin
from app.modules.exams.status import ExamStatus


class Exam(BaseModelMixin, Base):
    __tablename__ = "exams"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index]:
        return (
            Index(
                "uq_exams_class_title_active",
                "class_id",
                func.lower(cls.title),
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
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ExamStatus.DRAFT.value,
        server_default=text("'draft'"),
        index=True,
    )
    total_points: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    show_leaderboard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    allow_appeals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    show_feedback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    teacher = relationship("User")
    classroom = relationship("Classroom")


class ExamBlueprint(BaseModelMixin, Base):
    __tablename__ = "exam_blueprints"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    multiple_choice_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    short_answer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    essay_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    true_false_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    total_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")


class ExamToken(BaseModelMixin, Base):
    __tablename__ = "exam_tokens"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, ...]:
        return (
            Index("idx_exam_tokens_token", "token"),
            Index("idx_exam_tokens_exam_student", "exam_id", "student_id"),
            Index("idx_exam_tokens_class_id", "class_id"),
            Index("idx_exam_tokens_deleted_at", "deleted_at"),
            Index(
                "uq_exam_tokens_exam_student_active",
                "exam_id",
                "student_id",
                unique=True,
                postgresql_where=cls.deleted_at.is_(None),
            ),
        )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")
    student = relationship("Student")
