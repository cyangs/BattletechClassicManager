"""add full_name to weapons_master

Revision ID: 24e10da0a626
Revises: 61fb83d39948
Create Date: 2026-07-01 21:42:41.596639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24e10da0a626'
down_revision: Union[str, Sequence[str], None] = '61fb83d39948'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a human-readable full_name; the existing `name` becomes the SKU."""
    op.add_column('weapons_master', sa.Column('full_name', sa.String(length=100), nullable=True))
    # Backfill existing rows so the catalog shows a readable name immediately
    op.execute("UPDATE weapons_master SET full_name = name WHERE full_name IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('weapons_master', 'full_name')
