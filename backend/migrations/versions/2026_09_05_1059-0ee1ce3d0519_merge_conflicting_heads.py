"""merge conflicting heads

Revision ID: 0ee1ce3d0519
Revises: f2a3b4c5d6e7, g3h4i5j6k7l8
Create Date: 2026-09-05 10:59:28.962270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ee1ce3d0519'
down_revision: Union[str, Sequence[str], None] = ('f2a3b4c5d6e7', 'g3h4i5j6k7l8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
