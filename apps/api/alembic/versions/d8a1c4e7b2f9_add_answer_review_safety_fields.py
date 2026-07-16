"""Add answer review safety fields.

Revision ID: d8a1c4e7b2f9
Revises: c4a8e2f1b9d3
Create Date: 2026-07-12 00:00:00.000000

Existing AI feedback is intentionally preserved. Historical review rows keep
a null review reason because their original cause cannot be inferred safely.
"""

from alembic import op
import sqlalchemy as sa


revision = "d8a1c4e7b2f9"
down_revision = "c4a8e2f1b9d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("answers", sa.Column("teacher_feedback", sa.Text(), nullable=True))
    op.add_column("answers", sa.Column("review_reason_code", sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Downgrading intentionally removes the two UX-0A fields and any data
    # written to them after this migration was applied.
    op.drop_column("answers", "review_reason_code")
    op.drop_column("answers", "teacher_feedback")
