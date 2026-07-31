"""add session events and weapon states

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """History log of session events, plus per-unit weapon disable flags."""
    op.create_table(
        'session_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('turn', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('event_type', sa.String(length=30), nullable=False, server_default='fire'),
        sa.Column('session_mech_id', sa.Integer(), nullable=True),
        sa.Column('attacker', sa.String(length=100), nullable=True),
        sa.Column('target', sa.String(length=100), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_mech_id'], ['session_mechs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_session_events_session_id', 'session_events', ['session_id'])

    op.create_table(
        'session_weapon_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_mech_id', sa.Integer(), nullable=False),
        sa.Column('weapon_key', sa.String(length=50), nullable=False),
        sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['session_mech_id'], ['session_mechs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_mech_id', 'weapon_key', name='uq_session_weapon_instance'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('session_weapon_states')
    op.drop_index('ix_session_events_session_id', table_name='session_events')
    op.drop_table('session_events')
