"""add more fields to weapon attachments

Revision ID: afb8d7db97a2
Revises: d9e2f27b886e
Create Date: 2026-08-03 21:38:33.782422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afb8d7db97a2'
down_revision: Union[str, Sequence[str], None] = 'd9e2f27b886e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

enum_name = "attachmentType"

def upgrade() -> None:
    # 1. Create the ENUM type in the database first
    sa_enum = sa.Enum(
        "WEAPON", "MECH",
        name=enum_name
    )
    sa_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'weapon_attachments',
        sa.Column('attachment_type', sa_enum, nullable=True)
    )
    op.add_column(
        'weapon_attachments',
        sa.Column('cluster_modifier', sa.Integer, nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("weapon_attachments", "attachment_type")
    op.drop_column("weapon_attachments", "cluster_modifier")

