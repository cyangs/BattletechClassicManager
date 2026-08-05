"""add techbase to attachments

Revision ID: cddc80ea954d
Revises: afb8d7db97a2
Create Date: 2026-08-04 15:04:05.917494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cddc80ea954d'
down_revision: Union[str, Sequence[str], None] = 'afb8d7db97a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

enum_name = "techBaseEnum"

def upgrade() -> None:
    sa_enum = sa.Enum(
        "IS", "CLAN", "MIXED",
        name=enum_name
    )
    sa_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add the column referencing the newly created ENUM type
    op.add_column(
        'weapon_attachments',
        sa.Column('tech_base', sa_enum, nullable=True)
    )
    op.rename_table('weapon_attachments', 'attachments')


def downgrade() -> None:
    # 1. Drop the column first
    op.drop_column('weapon_attachments', 'tech_base')

    # 2. Drop the ENUM type from the database
    sa_enum = sa.Enum(name=enum_name)
    sa_enum.drop(op.get_bind(), checkfirst=True)

    op.rename_table('attachments', 'weapon_attachments')
