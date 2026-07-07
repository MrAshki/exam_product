"""create classes table

Revision ID: 5f1c3a27d9e4
Revises: 2b42dbb80b8f
Create Date: 2026-07-07 20:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5f1c3a27d9e4"
down_revision: Union[str, None] = "2b42dbb80b8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "classes",
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("academic_year", sa.String(length=50), nullable=True),
        sa.Column("grade_level", sa.String(length=50), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            name=op.f("fk_classes_teacher_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classes")),
    )
    op.create_index(op.f("ix_classes_deleted_at"), "classes", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_classes_teacher_id"), "classes", ["teacher_id"], unique=False)
    op.create_index(
        "uq_classes_teacher_title_active",
        "classes",
        ["teacher_id", sa.text("lower(title)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_classes_teacher_title_active", table_name="classes")
    op.drop_index(op.f("ix_classes_teacher_id"), table_name="classes")
    op.drop_index(op.f("ix_classes_deleted_at"), table_name="classes")
    op.drop_table("classes")
