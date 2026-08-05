"""add mech_attachment_link table

Revision ID: e1f2a3b4c5d6
Revises: cddc80ea954d
Create Date: 2026-08-04 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'cddc80ea954d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mech_attachment_link',
        sa.Column('mech_id', sa.Integer(), nullable=False),
        sa.Column('attachment_sku', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['mech_id'], ['mechs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attachment_sku'], ['attachments.sku'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('mech_id', 'attachment_sku'),
    )


def downgrade() -> None:
    op.drop_table('mech_attachment_link')
