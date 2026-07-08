"""create grade change logs table

Revision ID: e9b1c2d3f4a5
Revises: c6b7e23d4a91
Create Date: 2026-07-08 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e9b1c2d3f4a5"
down_revision: Union[str, None] = "c6b7e23d4a91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grade_change_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("old_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("new_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"], name=op.f("fk_grade_change_logs_answer_id_answers"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_grade_change_logs_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_grade_change_logs_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_grade_change_logs_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], name=op.f("fk_grade_change_logs_submission_id_submissions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_grade_change_logs_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grade_change_logs")),
    )
    op.create_index("idx_grade_change_logs_teacher_id", "grade_change_logs", ["teacher_id"], unique=False)
    op.create_index("idx_grade_change_logs_class_id", "grade_change_logs", ["class_id"], unique=False)
    op.create_index("idx_grade_change_logs_exam_id", "grade_change_logs", ["exam_id"], unique=False)
    op.create_index("idx_grade_change_logs_student_id", "grade_change_logs", ["student_id"], unique=False)
    op.create_index("idx_grade_change_logs_submission_id", "grade_change_logs", ["submission_id"], unique=False)
    op.create_index("idx_grade_change_logs_answer_id", "grade_change_logs", ["answer_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_grade_change_logs_answer_id", table_name="grade_change_logs")
    op.drop_index("idx_grade_change_logs_submission_id", table_name="grade_change_logs")
    op.drop_index("idx_grade_change_logs_student_id", table_name="grade_change_logs")
    op.drop_index("idx_grade_change_logs_exam_id", table_name="grade_change_logs")
    op.drop_index("idx_grade_change_logs_class_id", table_name="grade_change_logs")
    op.drop_index("idx_grade_change_logs_teacher_id", table_name="grade_change_logs")
    op.drop_table("grade_change_logs")
