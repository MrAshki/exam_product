"""create email logs table

Revision ID: 1e9a7b4c6d02
Revises: 7c3f2e91a4b8
Create Date: 2026-07-08 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "1e9a7b4c6d02"
down_revision: Union[str, None] = "7c3f2e91a4b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_email_logs_class_id_classes"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_email_logs_exam_id_exams"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_email_logs_student_id_students"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_email_logs_teacher_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_logs")),
    )
    op.create_index("idx_email_logs_teacher_id", "email_logs", ["teacher_id"], unique=False)
    op.create_index("idx_email_logs_class_id", "email_logs", ["class_id"], unique=False)
    op.create_index("idx_email_logs_exam_id", "email_logs", ["exam_id"], unique=False)
    op.create_index("idx_email_logs_student_id", "email_logs", ["student_id"], unique=False)
    op.create_index("idx_email_logs_type", "email_logs", ["type"], unique=False)
    op.create_index("idx_email_logs_status", "email_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_email_logs_status", table_name="email_logs")
    op.drop_index("idx_email_logs_type", table_name="email_logs")
    op.drop_index("idx_email_logs_student_id", table_name="email_logs")
    op.drop_index("idx_email_logs_exam_id", table_name="email_logs")
    op.drop_index("idx_email_logs_class_id", table_name="email_logs")
    op.drop_index("idx_email_logs_teacher_id", table_name="email_logs")
    op.drop_table("email_logs")
