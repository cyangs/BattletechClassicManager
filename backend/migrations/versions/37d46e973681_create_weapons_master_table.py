"""create weapons master table

Revision ID: 37d46e973681
Revises: 
Create Date: 2026-06-30 17:13:57.475607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d46e973681'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Code to execute when upgrading the database
    op.create_table(
        'weapons_master',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('use_ammo', sa.Boolean(), default=False),
        sa.Column('damage', sa.Integer(), nullable=True),
        sa.Column('heat', sa.Integer(), nullable=True),
        sa.Column('minimum_range', sa.Integer(), nullable=True),
        sa.Column('short_range', sa.Integer(), nullable=True),
        sa.Column('medium_range', sa.Integer(), nullable=True),
        sa.Column('long_range', sa.Integer(), nullable=True),
    )

def downgrade() -> None:
    # Code to execute if you need to undo this migration
    op.drop_table('weapons_master')
