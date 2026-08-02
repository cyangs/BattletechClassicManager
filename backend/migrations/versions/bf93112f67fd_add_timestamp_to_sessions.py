"""add timestamp to sessions

Revision ID: bf93112f67fd
Revises: cc85809b651b
Create Date: 2026-08-01 15:47:26.662636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf93112f67fd'
down_revision: Union[str, Sequence[str], None] = 'cc85809b651b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'game_sessions',
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=True),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("game_sessions", "created_on")
