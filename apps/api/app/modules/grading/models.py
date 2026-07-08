import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class GradeChangeLog(Base):
    __tablename__ = "grade_change_logs"
    __table_args__ = (
        Index("idx_grade_change_logs_teacher_id", "teacher_id"),
        Index("idx_grade_change_logs_class_id", "class_id"),
        Index("idx_grade_change_logs_exam_id", "exam_id"),
        Index("idx_grade_change_logs_student_id", "student_id"),
        Index("idx_grade_change_logs_submission_id", "submission_id"),
        Index("idx_grade_change_logs_answer_id", "answer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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
    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answers.id", ondelete="SET NULL"),
        nullable=True,
    )
    old_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    new_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")
    student = relationship("Student")
    submission = relationship("Submission")
    answer = relationship("Answer")
