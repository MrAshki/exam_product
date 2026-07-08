import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.base import Base, BaseModelMixin
from app.modules.appeals.status import AppealStatus


class Appeal(BaseModelMixin, Base):
    __tablename__ = "appeals"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, ...]:
        return (
            Index("idx_appeals_teacher_id", "teacher_id"),
            Index("idx_appeals_class_id", "class_id"),
            Index("idx_appeals_exam_id", "exam_id"),
            Index("idx_appeals_student_id", "student_id"),
            Index("idx_appeals_submission_id", "submission_id"),
            Index("idx_appeals_status", "status"),
            Index("idx_appeals_deleted_at", "deleted_at"),
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
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AppealStatus.PENDING.value,
        server_default=text("'pending'"),
    )
    teacher_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    new_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")
    student = relationship("Student")
    submission = relationship("Submission")
    answer = relationship("Answer")
