from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import TechBaseEnum

# Put the import here. Python ignores this at runtime, completely breaking the loop.
if TYPE_CHECKING:
    from weapon import MechWeapon
    from attachments import Attachments

class Mech(Base):
    __tablename__ = "mechs"
    # A chassis is identified by its name + variant model, so the same chassis
    # can exist in multiple configurations (e.g. "Turkina" Prime vs "Turkina" A).
    __table_args__ = (
        sa.UniqueConstraint("name", "model", name="uq_mechs_name_model"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tech_base: Mapped[TechBaseEnum] = mapped_column(
        sa.Enum(TechBaseEnum, name="techbaseenum", inherit_schema=True),
        nullable=False
    )
    model: Mapped[str] = mapped_column(String(50), nullable=True)
    tonnage: Mapped[int] = mapped_column(Integer, nullable=False)

    weapon_links: Mapped[List["MechWeapon"]] = relationship(
        back_populates="mech",
        cascade="all, delete-orphan"
    )

    # Chassis-level equipment (attachment_type "mech") fitted onto this mech.
    attachments: Mapped[List["Attachments"]] = relationship(
        secondary="mech_attachment_link"
    )
