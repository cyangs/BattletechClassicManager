"""add per-range-band damage and cluster/variable flags to weapons_master

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-29 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add short/medium/long range damage columns and the cluster / variable flags."""
    # Per-range-band damage (NULL -> fall back to the flat `damage` column).
    op.add_column('weapons_master', sa.Column('short_range_damage', sa.Integer(), nullable=True))
    op.add_column('weapons_master', sa.Column('medium_range_damage', sa.Integer(), nullable=True))
    op.add_column('weapons_master', sa.Column('long_range_damage', sa.Integer(), nullable=True))

    # Boolean flags. server_default backfills existing rows to False so the
    # NOT NULL constraint can be applied without a data migration.
    op.add_column(
        'weapons_master',
        sa.Column('variable_damage', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'weapons_master',
        sa.Column('cluster', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('weapons_master', 'cluster')
    op.drop_column('weapons_master', 'variable_damage')
    op.drop_column('weapons_master', 'long_range_damage')
    op.drop_column('weapons_master', 'medium_range_damage')
    op.drop_column('weapons_master', 'short_range_damage')
