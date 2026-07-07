import uuid

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.base import Base, BaseModelMixin


class Classroom(BaseModelMixin, Base):
    __tablename__ = "classes"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index]:
        return (
            Index(
                "uq_classes_teacher_title_active",
                "teacher_id",
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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    teacher = relationship("User")
