"""mech uniqueness on (name, model) to allow chassis variants

Revision ID: i5j6k7l8m9n0
Revises: h4i5j6k7l8m9
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'i5j6k7l8m9n0'
down_revision: Union[str, Sequence[str], None] = 'h4i5j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow the same chassis name with different variant models.

    Uniqueness moves from ``name`` alone to the pair ``(name, model)`` so e.g.
    "Turkina" Prime and "Turkina" A can both exist. The live schema never had a
    standalone unique index on ``name`` (it was declared on the model but not
    migrated), so this only *adds* the composite constraint.
    """
    op.create_unique_constraint('uq_mechs_name_model', 'mechs', ['name', 'model'])


def downgrade() -> None:
    op.drop_constraint('uq_mechs_name_model', 'mechs', type_='unique')
