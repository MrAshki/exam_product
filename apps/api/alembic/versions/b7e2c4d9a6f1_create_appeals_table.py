"""create appeals table

Revision ID: b7e2c4d9a6f1
Revises: f2d8a7c9b3e1
Create Date: 2026-07-08 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7e2c4d9a6f1"
down_revision: Union[str, None] = "f2d8a7c9b3e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appeals",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("teacher_response", sa.Text(), nullable=True),
        sa.Column("old_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("new_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"], name=op.f("fk_appeals_answer_id_answers"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_appeals_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_appeals_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_appeals_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], name=op.f("fk_appeals_submission_id_submissions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_appeals_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appeals")),
    )
    op.create_index("idx_appeals_teacher_id", "appeals", ["teacher_id"], unique=False)
    op.create_index("idx_appeals_class_id", "appeals", ["class_id"], unique=False)
    op.create_index("idx_appeals_exam_id", "appeals", ["exam_id"], unique=False)
    op.create_index("idx_appeals_student_id", "appeals", ["student_id"], unique=False)
    op.create_index("idx_appeals_submission_id", "appeals", ["submission_id"], unique=False)
    op.create_index("idx_appeals_status", "appeals", ["status"], unique=False)
    op.create_index("idx_appeals_deleted_at", "appeals", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_appeals_deleted_at"), "appeals", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_appeals_deleted_at"), table_name="appeals", if_exists=True)
    op.drop_index("idx_appeals_deleted_at", table_name="appeals")
    op.drop_index("idx_appeals_status", table_name="appeals")
    op.drop_index("idx_appeals_submission_id", table_name="appeals")
    op.drop_index("idx_appeals_student_id", table_name="appeals")
    op.drop_index("idx_appeals_exam_id", table_name="appeals")
    op.drop_index("idx_appeals_class_id", table_name="appeals")
    op.drop_index("idx_appeals_teacher_id", table_name="appeals")
    op.drop_table("appeals")
