from typing import Optional

from .base import Base

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Text, Enum, ARRAY
from .enums import AttachmentType, TechBaseEnum


class Attachments(Base):
    __tablename__ = "attachments"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True)  # "ARTEMISIV"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    to_hit_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cluster_modifier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tonnage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Describes what this is allowed on, Example ArtemisIV only allowed on MISSILE weapons
    allowed_on: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String()), nullable=True)

    attachment_type: Mapped[Optional[AttachmentType]] = mapped_column(
        Enum(AttachmentType, name="attachment_type"),
        nullable=False
    )

    tech_base: Mapped[Optional[TechBaseEnum]] = mapped_column(
        Enum(TechBaseEnum, name="techBaseEnum"),
        nullable=True
    )
