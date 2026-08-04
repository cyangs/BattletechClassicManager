from sqlalchemy import Table, Column, Integer, String, ForeignKey
from .base import Base

weapon_attachment_link = Table(
    "weapon_attachment_link",
    Base.metadata,
    Column("weapon_id", Integer, ForeignKey("weapons_master.id", ondelete="CASCADE"), primary_key=True),
    Column("attachment_sku", String(50), ForeignKey("weapon_attachments.sku", ondelete="CASCADE"),
           primary_key=True),
)

weapon_ammo_link = Table(
    "weapon_ammo_link",
    Base.metadata,
    Column("weapon_id", Integer, ForeignKey("weapons_master.id", ondelete="CASCADE"), primary_key=True),
    Column("ammo_sku", String(50), ForeignKey("ammo_types.sku", ondelete="CASCADE"), primary_key=True),
)