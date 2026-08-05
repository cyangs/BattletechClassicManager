"""add session-owned loadout tables

Gives each session its own copy of a deployed mech's weapons and attachments so
per-session damage (weapons/attachments destroyed) never mutates the master.

Revision ID: f2a3b4c5d6e7
Revises: 9e5b8f5daa46
Create Date: 2026-08-04 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = '9e5b8f5daa46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'session_mech_weapons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_mech_id', sa.Integer(), nullable=False),
        sa.Column('weapon_id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=50), nullable=False),
        sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('destroyed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['session_mech_id'], ['session_mechs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['weapon_id'], ['weapons_master.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'session_mech_attachments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_mech_id', sa.Integer(), nullable=False),
        sa.Column('attachment_sku', sa.String(length=50), nullable=False),
        sa.Column('destroyed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['session_mech_id'], ['session_mechs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attachment_sku'], ['attachments.sku'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('session_mech_attachments')
    op.drop_table('session_mech_weapons')
