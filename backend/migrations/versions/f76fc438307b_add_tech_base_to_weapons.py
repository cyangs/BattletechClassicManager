"""add tech base to weapons

Revision ID: f76fc438307b
Revises: daea3d504744
Create Date: 2026-08-03 17:30:22.584707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f76fc438307b'
down_revision: Union[str, Sequence[str], None] = 'daea3d504744'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


enum_name = "techBaseEnum"

def upgrade() -> None:
    # 1. Create the ENUM type in the database first
    sa_enum = sa.Enum(
        "INNER_SPHERE", "CLAN", "MIXED",
        name=enum_name
    )
    sa_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add the column referencing the newly created ENUM type
    op.add_column(
        'weapons_master',
        sa.Column('tech_base', sa_enum, nullable=True)
    )


def downgrade() -> None:
    # 1. Drop the column first
    op.drop_column('weapons_master', 'tech_base')

    # 2. Drop the ENUM type from the database
    sa_enum = sa.Enum(name=enum_name)
    sa_enum.drop(op.get_bind(), checkfirst=True)