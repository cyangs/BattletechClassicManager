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

    # Per-range-band damage for variable-damage weapons (e.g. pulse/clan gear).
    # NULL means "use the flat `damage` value at this band".
    short_range_damage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    medium_range_damage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    long_range_damage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # variable_damage: damage changes per range band (see *_range_damage above).
    variable_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Per-range-band to-hit modifiers. NULL means no bonus/penalty at that band.
    # e.g. variable pulse lasers: -3 short, -2 medium, -1 long.
    short_range_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    medium_range_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    long_range_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Cluster weapons: how many shots fire and the damage per cluster hit.
    # e.g. LRM 10 -> num_shots=10, cluster_damage=5; SRM 6 -> num_shots=6, cluster_damage=2.
    num_shots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cluster_damage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    @property
    def cluster(self) -> bool:
        """A weapon fires as a cluster (LRM/SRM etc.) when its cluster damage is set."""
        return self.cluster_damage is not None

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



