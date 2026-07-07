"""create exams blueprints questions

Revision ID: d4d0fb3f0c61
Revises: 8a0c7f3de921
Create Date: 2026-07-07 22:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4d0fb3f0c61"
down_revision: Union[str, None] = "8a0c7f3de921"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("total_points", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("show_leaderboard", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("allow_appeals", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("show_correct_answers", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("show_feedback", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_exams_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_exams_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exams")),
    )
    op.create_index(op.f("ix_exams_class_id"), "exams", ["class_id"], unique=False)
    op.create_index(op.f("ix_exams_deleted_at"), "exams", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_exams_status"), "exams", ["status"], unique=False)
    op.create_index(op.f("ix_exams_teacher_id"), "exams", ["teacher_id"], unique=False)
    op.create_index(
        "uq_exams_class_title_active",
        "exams",
        ["class_id", sa.text("lower(title)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "exam_blueprints",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("multiple_choice_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("short_answer_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("essay_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("true_false_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_question_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_exam_blueprints_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_exam_blueprints_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_exam_blueprints_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_blueprints")),
        sa.UniqueConstraint("exam_id", name=op.f("uq_exam_blueprints_exam_id")),
    )
    op.create_index(op.f("ix_exam_blueprints_class_id"), "exam_blueprints", ["class_id"], unique=False)
    op.create_index(op.f("ix_exam_blueprints_deleted_at"), "exam_blueprints", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_exam_blueprints_teacher_id"), "exam_blueprints", ["teacher_id"], unique=False)

    op.create_table(
        "questions",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'empty'"), nullable=False),
        sa.Column("source_type", sa.String(length=50), server_default=sa.text("'typed'"), nullable=False),
        sa.Column("input_method", sa.String(length=50), nullable=True),
        sa.Column("extraction_mode", sa.String(length=50), server_default=sa.text("'none'"), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("correct_answer_data", sa.JSON(), nullable=True),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("points", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("grading_instructions", sa.Text(), nullable=True),
        sa.Column("rubric", sa.JSON(), nullable=True),
        sa.Column("rubric_ai_suggested", sa.JSON(), nullable=True),
        sa.Column("rubric_teacher_confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("teacher_confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.Column("needs_teacher_review", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_questions_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_questions_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_questions_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
    )
    op.create_index(op.f("ix_questions_class_id"), "questions", ["class_id"], unique=False)
    op.create_index(op.f("ix_questions_deleted_at"), "questions", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_questions_exam_id"), "questions", ["exam_id"], unique=False)
    op.create_index(op.f("ix_questions_status"), "questions", ["status"], unique=False)
    op.create_index(op.f("ix_questions_teacher_id"), "questions", ["teacher_id"], unique=False)
    op.create_index(
        "uq_questions_exam_order_active",
        "questions",
        ["exam_id", "order_index"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "question_options",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("option_key", sa.String(length=20), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_question_options_class_id_classes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name=op.f("fk_question_options_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name=op.f("fk_question_options_question_id_questions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_question_options_teacher_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_options")),
    )
    op.create_index(op.f("ix_question_options_class_id"), "question_options", ["class_id"], unique=False)
    op.create_index(op.f("ix_question_options_deleted_at"), "question_options", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_question_options_exam_id"), "question_options", ["exam_id"], unique=False)
    op.create_index(op.f("ix_question_options_question_id"), "question_options", ["question_id"], unique=False)
    op.create_index(op.f("ix_question_options_teacher_id"), "question_options", ["teacher_id"], unique=False)
    op.create_index(
        "uq_question_options_question_key_active",
        "question_options",
        ["question_id", sa.text("lower(option_key)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_question_options_question_key_active", table_name="question_options")
    op.drop_index(op.f("ix_question_options_teacher_id"), table_name="question_options")
    op.drop_index(op.f("ix_question_options_question_id"), table_name="question_options")
    op.drop_index(op.f("ix_question_options_exam_id"), table_name="question_options")
    op.drop_index(op.f("ix_question_options_deleted_at"), table_name="question_options")
    op.drop_index(op.f("ix_question_options_class_id"), table_name="question_options")
    op.drop_table("question_options")
    op.drop_index("uq_questions_exam_order_active", table_name="questions")
    op.drop_index(op.f("ix_questions_teacher_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_status"), table_name="questions")
    op.drop_index(op.f("ix_questions_exam_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_deleted_at"), table_name="questions")
    op.drop_index(op.f("ix_questions_class_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("ix_exam_blueprints_teacher_id"), table_name="exam_blueprints")
    op.drop_index(op.f("ix_exam_blueprints_deleted_at"), table_name="exam_blueprints")
    op.drop_index(op.f("ix_exam_blueprints_class_id"), table_name="exam_blueprints")
    op.drop_table("exam_blueprints")
    op.drop_index("uq_exams_class_title_active", table_name="exams")
    op.drop_index(op.f("ix_exams_teacher_id"), table_name="exams")
    op.drop_index(op.f("ix_exams_status"), table_name="exams")
    op.drop_index(op.f("ix_exams_deleted_at"), table_name="exams")
    op.drop_index(op.f("ix_exams_class_id"), table_name="exams")
    op.drop_table("exams")
