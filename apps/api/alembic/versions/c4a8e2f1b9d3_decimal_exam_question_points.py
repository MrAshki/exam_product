"""Use decimal exam and question points.

Revision ID: c4a8e2f1b9d3
Revises: b7e2c4d9a6f1
Create Date: 2026-07-11 00:00:00.000000

Downgrade note:
    Converting NUMERIC(8,2) points back to INTEGER is inherently lossy.
    The downgrade uses ROUND(value)::integer explicitly rather than relying
    on implicit truncation.
"""

from alembic import op
import sqlalchemy as sa


revision = "c4a8e2f1b9d3"
down_revision = "b7e2c4d9a6f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "exams",
        "total_points",
        existing_type=sa.Integer(),
        type_=sa.Numeric(8, 2),
        existing_nullable=False,
        existing_server_default=sa.text("0"),
        server_default=sa.text("0"),
        postgresql_using="total_points::numeric(8,2)",
    )
    op.alter_column(
        "questions",
        "points",
        existing_type=sa.Integer(),
        type_=sa.Numeric(8, 2),
        existing_nullable=False,
        existing_server_default=sa.text("0"),
        server_default=sa.text("0"),
        postgresql_using="points::numeric(8,2)",
    )


def downgrade() -> None:
    op.alter_column(
        "questions",
        "points",
        existing_type=sa.Numeric(8, 2),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default=sa.text("0"),
        server_default=sa.text("0"),
        postgresql_using="ROUND(points)::integer",
    )
    op.alter_column(
        "exams",
        "total_points",
        existing_type=sa.Numeric(8, 2),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default=sa.text("0"),
        server_default=sa.text("0"),
        postgresql_using="ROUND(total_points)::integer",
    )
