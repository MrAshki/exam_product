"""create job logs table

Revision ID: 7c3f2e91a4b8
Revises: f2a6c9d8e1b4
Create Date: 2026-07-07 23:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7c3f2e91a4b8"
down_revision: Union[str, None] = "f2a6c9d8e1b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("queue_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'queued'"), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_job_logs_class_id_classes"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_job_logs_exam_id_exams"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name=op.f("fk_job_logs_question_id_questions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_job_logs_teacher_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_logs")),
    )
    op.create_index(op.f("ix_job_logs_celery_task_id"), "job_logs", ["celery_task_id"], unique=False)
    op.create_index(op.f("ix_job_logs_class_id"), "job_logs", ["class_id"], unique=False)
    op.create_index(op.f("ix_job_logs_entity_id"), "job_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_job_logs_exam_id"), "job_logs", ["exam_id"], unique=False)
    op.create_index(op.f("ix_job_logs_job_type"), "job_logs", ["job_type"], unique=False)
    op.create_index(op.f("ix_job_logs_question_id"), "job_logs", ["question_id"], unique=False)
    op.create_index(op.f("ix_job_logs_queue_name"), "job_logs", ["queue_name"], unique=False)
    op.create_index(op.f("ix_job_logs_status"), "job_logs", ["status"], unique=False)
    op.create_index(op.f("ix_job_logs_submission_id"), "job_logs", ["submission_id"], unique=False)
    op.create_index(op.f("ix_job_logs_teacher_id"), "job_logs", ["teacher_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_logs_teacher_id"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_submission_id"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_status"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_queue_name"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_question_id"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_job_type"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_exam_id"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_entity_id"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_class_id"), table_name="job_logs")
    op.drop_index(op.f("ix_job_logs_celery_task_id"), table_name="job_logs")
    op.drop_table("job_logs")
