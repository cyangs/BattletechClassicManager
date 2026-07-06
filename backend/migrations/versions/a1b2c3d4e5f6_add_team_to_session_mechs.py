"""add team to session_mechs

Revision ID: a1b2c3d4e5f6
Revises: 9270cd514f59
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9270cd514f59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tag each deployed unit with the side it fights for (player or enemy)."""
    op.add_column(
        'session_mechs',
        sa.Column('team', sa.String(length=20), nullable=False, server_default='player'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('session_mechs', 'team')
