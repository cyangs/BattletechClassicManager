from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.sql.schema import ForeignKey

from database.models.base import Base

# This prevents Python from actually importing Mech at runtime, breaking the loop
if TYPE_CHECKING:
    from mech import Mech

class Weapon(Base):
    """Maps directly to the weapons_master database table."""
    __tablename__ = "weapons_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)  # internal SKU, e.g. "CLERLargeLaser"
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # display name for the catalog
    use_ammo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    damage: Mapped[int] = mapped_column(Integer, nullable=False)
    heat: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_range: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    short_range: Mapped[int] = mapped_column(Integer, nullable=True)
    medium_range: Mapped[int] = mapped_column(Integer, nullable=True)
    long_range: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Weapon(name='{self.name}', damage={self.damage}, heat={self.heat})>"


class MechWeapon(Base):
    """Bridge table tracking counts and placement."""
    __tablename__ = "mech_weapons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mech_id: Mapped[int] = mapped_column(ForeignKey("mechs.id", ondelete="CASCADE"), nullable=False)
    weapon_id: Mapped[int] = mapped_column(ForeignKey("weapons_master.id", ondelete="RESTRICT"), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    location: Mapped[str] = mapped_column(String(50), nullable=False)

    # Use string references ("Mech") to prevent circular imports!
    mech: Mapped["Mech"] = relationship(back_populates="weapon_links")
    weapon: Mapped["Weapon"] = relationship()