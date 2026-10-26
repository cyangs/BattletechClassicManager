from typing import Optional, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .mech import Mech


class AlphaStrikeCard(Base):
    """The Alpha Strike stat card for a chassis.

    One row per :class:`~database.models.mech.Mech` (1:1), so a chassis can have
    both a Classic loadout (weapon_links/attachments) and an Alpha Strike card.
    Unlike Classic, an AS unit's entire offense/defense is a handful of small
    integers rather than individual weapons — hence a flat stat table.
    """
    __tablename__ = "alpha_strike_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 1:1 with the chassis. Unique so a mech can't have two cards; cascade so a
    # deleted chassis takes its card with it.
    mech_id: Mapped[int] = mapped_column(
        sa.ForeignKey("mechs.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Force-building / identity
    point_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # PV
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)         # 1-4
    role: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)      # Skirmisher, Sniper, ...

    # Movement
    move: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)         # inches
    move_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True) # "", "j" (jump), ...
    tmm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)          # target movement modifier it imposes

    # Offense — bracket damage (0-6+ each). These cap the dice in variable mode.
    damage_short: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damage_medium: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damage_long: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overheat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)   # extra dmg from heat

    # Defense — small-integer pip tracks
    armor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    structure: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Special ability codes (e.g. ["AMS", "ECM"]). Stored, not resolved in v1.
    specials: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    mech: Mapped["Mech"] = relationship(back_populates="alpha_strike_card")
