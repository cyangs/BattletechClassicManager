"""add restrictions to attachments

Revision ID: 9e5b8f5daa46
Revises: e1f2a3b4c5d6
Create Date: 2026-08-04 19:34:44.179097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e5b8f5daa46'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


enum_name = "weaponType"

def upgrade() -> None:
    sa_enum = sa.Enum(
        "MISSILE", "BALLISTIC", "LASER", "PPC", "ARTY", "OTHER",
        name=enum_name
    )
    sa_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add the column referencing the newly created ENUM type
    op.add_column(
        'weapons_master',
        sa.Column('type', sa_enum, nullable=True)
    )
    op.add_column(
        'attachments',
        sa.Column('allowed_on', sa.ARRAY(sa.String()), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('weapons_master', 'type')
    op.drop_column('attachments', 'allowed_on')
