"""initial empty migration

Revision ID: 69d85c845e06
Revises: 
Create Date: 2026-07-07 18:36:03.281060
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '69d85c845e06'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
