"""create result and leaderboard tokens

Revision ID: f2d8a7c9b3e1
Revises: e9b1c2d3f4a5
Create Date: 2026-07-08 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f2d8a7c9b3e1"
down_revision: Union[str, None] = "e9b1c2d3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "result_tokens",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_result_tokens_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_result_tokens_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_result_tokens_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], name=op.f("fk_result_tokens_submission_id_submissions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_result_tokens_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_result_tokens")),
        sa.UniqueConstraint("token", name=op.f("uq_result_tokens_token")),
    )
    op.create_index("idx_result_tokens_token", "result_tokens", ["token"], unique=False)
    op.create_index("idx_result_tokens_submission_id", "result_tokens", ["submission_id"], unique=False)
    op.create_index("idx_result_tokens_exam_student", "result_tokens", ["exam_id", "student_id"], unique=False)
    op.create_index("idx_result_tokens_deleted_at", "result_tokens", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_result_tokens_deleted_at"), "result_tokens", ["deleted_at"], unique=False)
    op.create_index(
        "uq_result_tokens_submission_active",
        "result_tokens",
        ["submission_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "leaderboard_tokens",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_leaderboard_tokens_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_leaderboard_tokens_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_leaderboard_tokens_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_leaderboard_tokens")),
        sa.UniqueConstraint("token", name=op.f("uq_leaderboard_tokens_token")),
    )
    op.create_index("idx_leaderboard_tokens_token", "leaderboard_tokens", ["token"], unique=False)
    op.create_index("idx_leaderboard_tokens_class_exam", "leaderboard_tokens", ["class_id", "exam_id"], unique=False)
    op.create_index("idx_leaderboard_tokens_deleted_at", "leaderboard_tokens", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_leaderboard_tokens_deleted_at"), "leaderboard_tokens", ["deleted_at"], unique=False)
    op.create_index(
        "uq_leaderboard_tokens_class_exam_active",
        "leaderboard_tokens",
        ["class_id", "exam_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_leaderboard_tokens_class_exam_active", table_name="leaderboard_tokens")
    op.drop_index(op.f("ix_leaderboard_tokens_deleted_at"), table_name="leaderboard_tokens", if_exists=True)
    op.drop_index("idx_leaderboard_tokens_deleted_at", table_name="leaderboard_tokens")
    op.drop_index("idx_leaderboard_tokens_class_exam", table_name="leaderboard_tokens")
    op.drop_index("idx_leaderboard_tokens_token", table_name="leaderboard_tokens")
    op.drop_table("leaderboard_tokens")

    op.drop_index("uq_result_tokens_submission_active", table_name="result_tokens")
    op.drop_index(op.f("ix_result_tokens_deleted_at"), table_name="result_tokens", if_exists=True)
    op.drop_index("idx_result_tokens_deleted_at", table_name="result_tokens")
    op.drop_index("idx_result_tokens_exam_student", table_name="result_tokens")
    op.drop_index("idx_result_tokens_submission_id", table_name="result_tokens")
    op.drop_index("idx_result_tokens_token", table_name="result_tokens")
    op.drop_table("result_tokens")
