"""add weapon modifiers and clustering

Revision ID: cc85809b651b
Revises: d4e5f6a7b8c9
Create Date: 2026-07-30 21:25:25.530076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc85809b651b'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adds weapon modifiers at ranges. Ex. Variable Pulse Lasers are -1 at long, -2 at medium, -3 at short"""
    op.add_column('weapons_master', sa.Column('short_range_modifier', sa.Integer, nullable=True))
    op.add_column('weapons_master', sa.Column('medium_range_modifier', sa.Integer, nullable=True))
    op.add_column('weapons_master', sa.Column('long_range_modifier', sa.Integer, nullable=True))

    """Adds number of shots, and clustering
    Example: LRM 10 would have 10 shots, rolling on the 10 table. Cluster Damage of 5.
    Example: SRM 6 would have 6 shots, rolling on the 6 table. Cluster Damage of 2"""
    op.add_column('weapons_master', sa.Column('num_shots', sa.Integer, nullable=True))
    op.add_column('weapons_master', sa.Column('cluster_damage', sa.Integer, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('weapons_master', 'short_range_modifier')
    op.drop_column('weapons_master', 'medium_range_modifier')
    op.drop_column('weapons_master', 'long_range_modifier')
    op.drop_column('weapons_master', 'num_shots')
    op.drop_column('weapons_master', 'cluster_damage')
