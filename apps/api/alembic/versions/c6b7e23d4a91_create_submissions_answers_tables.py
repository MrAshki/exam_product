"""create submissions answers tables

Revision ID: c6b7e23d4a91
Revises: a83f4d2c9e10
Create Date: 2026-07-08 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c6b7e23d4a91"
down_revision: Union[str, None] = "a83f4d2c9e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'not_started'"), nullable=False),
        sa.Column("total_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("ai_confidence_avg", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("needs_review_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("teacher_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_submissions_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_submissions_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_submissions_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_submissions_teacher_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["token_id"], ["exam_tokens.id"], name=op.f("fk_submissions_token_id_exam_tokens"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submissions")),
    )
    op.create_index("idx_submissions_teacher_id", "submissions", ["teacher_id"], unique=False)
    op.create_index("idx_submissions_class_id", "submissions", ["class_id"], unique=False)
    op.create_index("idx_submissions_exam_id", "submissions", ["exam_id"], unique=False)
    op.create_index("idx_submissions_student_id", "submissions", ["student_id"], unique=False)
    op.create_index("idx_submissions_exam_student", "submissions", ["exam_id", "student_id"], unique=False)
    op.create_index("idx_submissions_status", "submissions", ["status"], unique=False)
    op.create_index("idx_submissions_deleted_at", "submissions", ["deleted_at"], unique=False)
    op.create_index(
        "uq_submissions_exam_student_active",
        "submissions",
        ["exam_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "answers",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_answer", sa.Text(), nullable=True),
        sa.Column("answer_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("auto_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("teacher_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("final_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("ai_feedback", sa.Text(), nullable=True),
        sa.Column("ai_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("needs_review", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reviewed_by_teacher", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_answers_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_answers_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name=op.f("fk_answers_question_id_questions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_answers_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], name=op.f("fk_answers_submission_id_submissions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_answers_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answers")),
    )
    op.create_index("idx_answers_teacher_id", "answers", ["teacher_id"], unique=False)
    op.create_index("idx_answers_class_id", "answers", ["class_id"], unique=False)
    op.create_index("idx_answers_exam_id", "answers", ["exam_id"], unique=False)
    op.create_index("idx_answers_student_id", "answers", ["student_id"], unique=False)
    op.create_index("idx_answers_submission_id", "answers", ["submission_id"], unique=False)
    op.create_index("idx_answers_question_id", "answers", ["question_id"], unique=False)
    op.create_index("idx_answers_needs_review", "answers", ["needs_review"], unique=False)
    op.create_index("idx_answers_deleted_at", "answers", ["deleted_at"], unique=False)
    op.create_index(
        "uq_answers_submission_question_active",
        "answers",
        ["submission_id", "question_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_answers_submission_question_active", table_name="answers")
    op.drop_index("idx_answers_deleted_at", table_name="answers")
    op.drop_index("idx_answers_needs_review", table_name="answers")
    op.drop_index("idx_answers_question_id", table_name="answers")
    op.drop_index("idx_answers_submission_id", table_name="answers")
    op.drop_index("idx_answers_student_id", table_name="answers")
    op.drop_index("idx_answers_exam_id", table_name="answers")
    op.drop_index("idx_answers_class_id", table_name="answers")
    op.drop_index("idx_answers_teacher_id", table_name="answers")
    op.drop_table("answers")
    op.drop_index("uq_submissions_exam_student_active", table_name="submissions")
    op.drop_index("idx_submissions_deleted_at", table_name="submissions")
    op.drop_index("idx_submissions_status", table_name="submissions")
    op.drop_index("idx_submissions_exam_student", table_name="submissions")
    op.drop_index("idx_submissions_student_id", table_name="submissions")
    op.drop_index("idx_submissions_exam_id", table_name="submissions")
    op.drop_index("idx_submissions_class_id", table_name="submissions")
    op.drop_index("idx_submissions_teacher_id", table_name="submissions")
    op.drop_table("submissions")
