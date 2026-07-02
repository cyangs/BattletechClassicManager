"""add current_turn to game_sessions

Revision ID: 9270cd514f59
Revises: 24e10da0a626
Create Date: 2026-07-01 22:11:17.673161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9270cd514f59'
down_revision: Union[str, Sequence[str], None] = '24e10da0a626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Track the active turn number for a game session (0 = not yet started)."""
    op.add_column(
        'game_sessions',
        sa.Column('current_turn', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('game_sessions', 'current_turn')
