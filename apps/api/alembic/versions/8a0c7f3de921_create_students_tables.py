"""create students tables

Revision ID: 8a0c7f3de921
Revises: 5f1c3a27d9e4
Create Date: 2026-07-07 21:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8a0c7f3de921"
down_revision: Union[str, None] = "5f1c3a27d9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("student_code", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("teacher_note", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            name=op.f("fk_students_teacher_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_students")),
    )
    op.create_index(op.f("ix_students_deleted_at"), "students", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_students_teacher_id"), "students", ["teacher_id"], unique=False)
    op.create_index(
        "uq_students_teacher_email_active",
        "students",
        ["teacher_id", sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "class_students",
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["class_id"],
            ["classes.id"],
            name=op.f("fk_class_students_class_id_classes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_class_students_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_class_students")),
    )
    op.create_index(op.f("ix_class_students_class_id"), "class_students", ["class_id"], unique=False)
    op.create_index(op.f("ix_class_students_deleted_at"), "class_students", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_class_students_student_id"), "class_students", ["student_id"], unique=False)
    op.create_index(
        "uq_class_students_active_membership",
        "class_students",
        ["class_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_class_students_active_membership", table_name="class_students")
    op.drop_index(op.f("ix_class_students_student_id"), table_name="class_students")
    op.drop_index(op.f("ix_class_students_deleted_at"), table_name="class_students")
    op.drop_index(op.f("ix_class_students_class_id"), table_name="class_students")
    op.drop_table("class_students")
    op.drop_index("uq_students_teacher_email_active", table_name="students")
    op.drop_index(op.f("ix_students_teacher_id"), table_name="students")
    op.drop_index(op.f("ix_students_deleted_at"), table_name="students")
    op.drop_table("students")
