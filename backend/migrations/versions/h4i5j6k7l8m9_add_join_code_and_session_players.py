"""add join_code to sessions and create session_players

Revision ID: h4i5j6k7l8m9
Revises: 0ee1ce3d0519
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h4i5j6k7l8m9'
down_revision: Union[str, Sequence[str], None] = '0ee1ce3d0519'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Multiplayer step 1: shareable join code + per-session players.

    ``join_code`` lets players join a session by a shared code. ``session_players``
    is the durable "who is acting" record — unit ownership and turn logic will
    key off it. ``user_id`` is reserved (nullable) for a future accounts system.
    """
    op.add_column(
        'game_sessions',
        sa.Column('join_code', sa.String(length=36), nullable=True),
    )
    op.create_unique_constraint(
        'uq_game_sessions_join_code', 'game_sessions', ['join_code']
    )

    op.create_table(
        'session_players',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('player_token', sa.String(length=64), nullable=False),
        sa.Column('side', sa.String(length=30), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('player_token', name='uq_session_players_token'),
    )


def downgrade() -> None:
    op.drop_table('session_players')
    op.drop_constraint('uq_game_sessions_join_code', 'game_sessions', type_='unique')
    op.drop_column('game_sessions', 'join_code')
