"""add weapon modifications column

Revision ID: daea3d504744
Revises: bf93112f67fd
Create Date: 2026-08-03 16:57:53.211876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daea3d504744'
down_revision: Union[str, Sequence[str], None] = 'bf93112f67fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adds a JSON column named 'modifications' to the 'weapons_master' table
    # Usage would be a dict with keys and values.
    # For example UACs would have the ULTRA keyword
    # Artemis would have the ARTEMIS keyword
    op.add_column(
        'weapons_master',
        sa.Column('modifications', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("weapons_master", "modifications")

