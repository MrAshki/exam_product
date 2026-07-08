import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.base import Base, BaseModelMixin
from app.modules.submissions.status import SubmissionStatus


class Submission(BaseModelMixin, Base):
    __tablename__ = "submissions"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, ...]:
        return (
            Index("idx_submissions_teacher_id", "teacher_id"),
            Index("idx_submissions_class_id", "class_id"),
            Index("idx_submissions_exam_id", "exam_id"),
            Index("idx_submissions_student_id", "student_id"),
            Index("idx_submissions_exam_student", "exam_id", "student_id"),
            Index("idx_submissions_status", "status"),
            Index("idx_submissions_deleted_at", "deleted_at"),
            Index(
                "uq_submissions_exam_student_active",
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
    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_tokens.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SubmissionStatus.NOT_STARTED.value,
        server_default=text("'not_started'"),
    )
    total_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    ai_confidence_avg: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    needs_review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    teacher_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")
    student = relationship("Student")
    token = relationship("ExamToken")


class Answer(BaseModelMixin, Base):
    __tablename__ = "answers"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, ...]:
        return (
            Index("idx_answers_teacher_id", "teacher_id"),
            Index("idx_answers_class_id", "class_id"),
            Index("idx_answers_exam_id", "exam_id"),
            Index("idx_answers_student_id", "student_id"),
            Index("idx_answers_submission_id", "submission_id"),
            Index("idx_answers_question_id", "question_id"),
            Index("idx_answers_needs_review", "needs_review"),
            Index("idx_answers_deleted_at", "deleted_at"),
            Index(
                "uq_answers_submission_question_active",
                "submission_id",
                "question_id",
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
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_data: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    auto_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    teacher_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    final_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    reviewed_by_teacher: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")
    student = relationship("Student")
    submission = relationship("Submission")
    question = relationship("Question")

