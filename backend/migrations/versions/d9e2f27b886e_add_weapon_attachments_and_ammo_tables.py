"""add weapon attachments and ammo tables

Revision ID: d9e2f27b886e
Revises: f76fc438307b
Create Date: 2026-08-03 17:37:13.954384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e2f27b886e'
down_revision: Union[str, Sequence[str], None] = 'f76fc438307b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # --- Attachments (Artemis IV, Targeting Computer, TAG, etc.) ---
    op.create_table(
        "weapon_attachments",
        sa.Column("sku", sa.String(length=50), primary_key=True),  # e.g. "ARTEMISIV"
        sa.Column("display_name", sa.String(length=100), nullable=False),  # e.g. "Artemis IV FCS"
        sa.Column("to_hit_modifier", sa.Integer, nullable=True),
        sa.Column("tonnage", sa.Float, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
    )

    # --- Ammo types (Standard, Inferno, Swarm, etc.) ---
    op.create_table(
        "ammo_types",
        sa.Column("sku", sa.String(length=50), primary_key=True),  # e.g. "INFERNO"
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("damage", sa.Integer, nullable=True),
        sa.Column("heat", sa.Integer, nullable=True),
        sa.Column("special_effect", sa.String(length=50), nullable=True),  # e.g. "fire", "anti_infantry"
        sa.Column("description", sa.Text, nullable=True),
    )

    # --- Link table: weapon <-> attachments (many-to-many) ---
    op.create_table(
        "weapon_attachment_link",
        sa.Column(
            "weapon_id",
            sa.Integer,
            sa.ForeignKey("weapons_master.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "attachment_sku",
            sa.String(length=50),
            sa.ForeignKey("weapon_attachments.sku", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # --- Link table: weapon <-> compatible ammo (many-to-many) ---
    op.create_table(
        "weapon_ammo_link",
        sa.Column(
            "weapon_id",
            sa.Integer,
            sa.ForeignKey("weapons_master.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "ammo_sku",
            sa.String(length=50),
            sa.ForeignKey("ammo_types.sku", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("weapon_ammo_link")
    op.drop_table("weapon_attachment_link")
    op.drop_table("ammo_types")
    op.drop_table("weapon_attachments")