"""add accent_color to session_mechs

Revision ID: g3h4i5j6k7l8
Revises: f76fc438307b
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g3h4i5j6k7l8'
down_revision: Union[str, Sequence[str], None] = 'f76fc438307b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional accent colour to each deployed unit.

    NULL means no colour has been chosen (the default grey card appearance).
    Stored as a short label string matching the frontend palette keys
    (e.g. 'amber', 'sky', 'rose') rather than a raw hex value so the UI
    theme controls the actual rendering.
    """
    op.add_column(
        'session_mechs',
        sa.Column('accent_color', sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('session_mechs', 'accent_color')
