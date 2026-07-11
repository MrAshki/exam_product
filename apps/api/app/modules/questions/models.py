import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, func, text as sa_text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.base import Base, BaseModelMixin
from app.modules.exams.status import ExtractionMode, QuestionSourceType, QuestionStatus


class Question(BaseModelMixin, Base):
    __tablename__ = "questions"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index]:
        return (
            Index(
                "uq_questions_exam_order_active",
                "exam_id",
                "order_index",
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
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=QuestionStatus.EMPTY.value,
        server_default=sa_text("'empty'"),
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=QuestionSourceType.TYPED.value,
        server_default=sa_text("'typed'"),
    )
    input_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extraction_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ExtractionMode.NONE.value,
        server_default=sa_text("'none'"),
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer_data: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=sa_text("0"),
    )
    grading_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    rubric_ai_suggested: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    rubric_teacher_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa_text("false"),
    )
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    teacher_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa_text("false"),
    )
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_teacher_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa_text("false"),
    )

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")


class QuestionOption(BaseModelMixin, Base):
    __tablename__ = "question_options"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index]:
        return (
            Index(
                "uq_question_options_question_key_active",
                "question_id",
                func.lower(cls.option_key),
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
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_key: Mapped[str] = mapped_column(String(20), nullable=False)
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa_text("false"),
    )

    teacher = relationship("User")
    classroom = relationship("Classroom")
    exam = relationship("Exam")
    question = relationship("Question")
