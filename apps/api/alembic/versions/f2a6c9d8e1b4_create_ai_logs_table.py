"""create ai logs table

Revision ID: f2a6c9d8e1b4
Revises: d4d0fb3f0c61
Create Date: 2026-07-07 23:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f2a6c9d8e1b4"
down_revision: Union[str, None] = "d4d0fb3f0c61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_name", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("request_json", sa.JSON(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_ai_logs_class_id_classes"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_ai_logs_exam_id_exams"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name=op.f("fk_ai_logs_question_id_questions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_ai_logs_teacher_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_logs")),
    )
    op.create_index(op.f("ix_ai_logs_class_id"), "ai_logs", ["class_id"], unique=False)
    op.create_index(op.f("ix_ai_logs_exam_id"), "ai_logs", ["exam_id"], unique=False)
    op.create_index(op.f("ix_ai_logs_question_id"), "ai_logs", ["question_id"], unique=False)
    op.create_index(op.f("ix_ai_logs_status"), "ai_logs", ["status"], unique=False)
    op.create_index(op.f("ix_ai_logs_task_name"), "ai_logs", ["task_name"], unique=False)
    op.create_index(op.f("ix_ai_logs_teacher_id"), "ai_logs", ["teacher_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_logs_teacher_id"), table_name="ai_logs")
    op.drop_index(op.f("ix_ai_logs_task_name"), table_name="ai_logs")
    op.drop_index(op.f("ix_ai_logs_status"), table_name="ai_logs")
    op.drop_index(op.f("ix_ai_logs_question_id"), table_name="ai_logs")
    op.drop_index(op.f("ix_ai_logs_exam_id"), table_name="ai_logs")
    op.drop_index(op.f("ix_ai_logs_class_id"), table_name="ai_logs")
    op.drop_table("ai_logs")
