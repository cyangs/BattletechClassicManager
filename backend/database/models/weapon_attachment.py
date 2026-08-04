from typing import Optional

from .base import Base

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Text, Enum
from .enums import AttachmentType


class WeaponAttachment(Base):
    __tablename__ = "weapon_attachments"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True)  # "ARTEMISIV"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    to_hit_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cluster_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tonnage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    attachment_type: Mapped[Optional[AttachmentType]] = mapped_column(
        Enum(AttachmentType, name="attachment_type"),
        nullable=False
    )
