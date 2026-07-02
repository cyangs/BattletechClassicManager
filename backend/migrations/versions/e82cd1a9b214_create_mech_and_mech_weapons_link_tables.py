"""create mech and mech weapons link tables

Revision ID: e82cd1a9b214
Revises: 37d46e973681
Create Date: 2026-06-30 19:44:18.002466

"""
from typing import Sequence, Union
from database.models.enums import TechBaseEnum

# revision identifiers, used by Alembic.
revision: str = 'e82cd1a9b214'
down_revision: Union[str, Sequence[str], None] = '37d46e973681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 1. Create Mechs Table
    op.create_table(
        'mechs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=False),
        sa.Column('tech_base', sa.Enum(TechBaseEnum), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('tonnage', sa.Integer(), nullable=False)
    )

    # 2. Create Mech Weapons Link Table
    op.create_table(
        'mech_weapons',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('mech_id', sa.Integer(), nullable=False),
        sa.Column('weapon_id', sa.Integer(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('location', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['mech_id'], ['mechs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['weapon_id'], ['weapons_master.id'], ondelete='RESTRICT')
    )


def downgrade() -> None:
    op.drop_table('mech_weapons')
    op.drop_table('mechs')