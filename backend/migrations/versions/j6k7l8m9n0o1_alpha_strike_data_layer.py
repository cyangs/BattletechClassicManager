"""alpha strike data layer: cards table + session/session_mech columns

Revision ID: j6k7l8m9n0o1
Revises: i5j6k7l8m9n0
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j6k7l8m9n0o1'
down_revision: Union[str, Sequence[str], None] = 'i5j6k7l8m9n0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Foundation for Alpha Strike: a per-chassis stat card plus session
    discriminators and per-unit AS combat state. All additive — Classic is
    untouched (new table + new columns, existing ones unchanged)."""
    op.create_table(
        'alpha_strike_cards',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('mech_id', sa.Integer(), nullable=False),
        sa.Column('point_value', sa.Integer(), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(length=40), nullable=True),
        sa.Column('move', sa.Integer(), nullable=True),
        sa.Column('move_type', sa.String(length=10), nullable=True),
        sa.Column('tmm', sa.Integer(), nullable=True),
        sa.Column('damage_short', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('damage_medium', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('damage_long', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overheat', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('armor', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('structure', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('specials', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['mech_id'], ['mechs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('mech_id', name='uq_alpha_strike_cards_mech_id'),
    )

    # Session-level: which system + (AS only) which damage mode.
    op.add_column(
        'game_sessions',
        sa.Column('game_system', sa.String(length=20), nullable=False, server_default='classic'),
    )
    op.add_column(
        'game_sessions',
        sa.Column('as_damage_mode', sa.String(length=20), nullable=False, server_default='standard'),
    )

    # Per-unit AS combat state (nullable; populated only for AS sessions).
    op.add_column('session_mechs', sa.Column('as_armor_current', sa.Integer(), nullable=True))
    op.add_column('session_mechs', sa.Column('as_structure_current', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('session_mechs', 'as_structure_current')
    op.drop_column('session_mechs', 'as_armor_current')
    op.drop_column('game_sessions', 'as_damage_mode')
    op.drop_column('game_sessions', 'game_system')
    op.drop_table('alpha_strike_cards')
