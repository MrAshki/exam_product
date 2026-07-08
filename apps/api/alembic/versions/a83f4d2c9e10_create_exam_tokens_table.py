"""create exam tokens table

Revision ID: a83f4d2c9e10
Revises: 1e9a7b4c6d02
Create Date: 2026-07-08 13:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a83f4d2c9e10"
down_revision: Union[str, None] = "1e9a7b4c6d02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exam_tokens",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_exam_tokens_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_exam_tokens_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_exam_tokens_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_exam_tokens_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_tokens")),
        sa.UniqueConstraint("token", name=op.f("uq_exam_tokens_token")),
    )
    op.create_index("idx_exam_tokens_token", "exam_tokens", ["token"], unique=False)
    op.create_index("idx_exam_tokens_exam_student", "exam_tokens", ["exam_id", "student_id"], unique=False)
    op.create_index("idx_exam_tokens_class_id", "exam_tokens", ["class_id"], unique=False)
    op.create_index("idx_exam_tokens_deleted_at", "exam_tokens", ["deleted_at"], unique=False)
    op.create_index(
        "uq_exam_tokens_exam_student_active",
        "exam_tokens",
        ["exam_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_exam_tokens_exam_student_active", table_name="exam_tokens")
    op.drop_index("idx_exam_tokens_deleted_at", table_name="exam_tokens")
    op.drop_index("idx_exam_tokens_class_id", table_name="exam_tokens")
    op.drop_index("idx_exam_tokens_exam_student", table_name="exam_tokens")
    op.drop_index("idx_exam_tokens_token", table_name="exam_tokens")
    op.drop_table("exam_tokens")
