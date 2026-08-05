from sqlalchemy import Table, Column, Integer, String, ForeignKey
from .base import Base

weapon_attachment_link = Table(
    "weapon_attachment_link",
    Base.metadata,
    Column("weapon_id", Integer, ForeignKey("weapons_master.id", ondelete="CASCADE"), primary_key=True),
    Column("attachment_sku", String(50), ForeignKey("attachments.sku", ondelete="CASCADE"),
           primary_key=True),
)

weapon_ammo_link = Table(
    "weapon_ammo_link",
    Base.metadata,
    Column("weapon_id", Integer, ForeignKey("weapons_master.id", ondelete="CASCADE"), primary_key=True),
    Column("ammo_sku", String(50), ForeignKey("ammo_types.sku", ondelete="CASCADE"), primary_key=True),
)

# Chassis-level equipment fitted onto a mech (attachment_type "mech"), e.g. a
# targeting computer. A mech either has a given attachment or it doesn't, so a
# plain many-to-many join keyed on (mech_id, attachment_sku) is enough.
mech_attachment_link = Table(
    "mech_attachment_link",
    Base.metadata,
    Column("mech_id", Integer, ForeignKey("mechs.id", ondelete="CASCADE"), primary_key=True),
    Column("attachment_sku", String(50), ForeignKey("attachments.sku", ondelete="CASCADE"),
           primary_key=True),
)