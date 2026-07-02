"""create game sessions and session mechs tables

Revision ID: 61fb83d39948
Revises: e82cd1a9b214
Create Date: 2026-06-30 23:54:40.015923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '61fb83d39948'
down_revision: Union[str, Sequence[str], None] = 'e82cd1a9b214'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the main Game Sessions table
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active')
    )

    # 2. Create the Session Mechs tracking roster table
    op.create_table(
        'session_mechs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('mech_id', sa.Integer(), nullable=False),

        # Setup foreign keys to link to your existing data
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mech_id'], ['mechs.id'], ondelete='RESTRICT')
    )

def downgrade() -> None:
    # Undo operations in exact reverse order to prevent constraint crashes
    op.drop_table('session_mechs')
    op.drop_table('game_sessions')