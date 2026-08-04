from typing import Optional

from .base import Base

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text


class AmmoType(Base):
    __tablename__ = "ammo_types"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True)  # "INFERNO"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    damage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    heat: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    special_effect: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

