from typing import List, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base

# Imported only for type-checking to avoid a runtime circular import loop.
if TYPE_CHECKING:
    from database.models.mech import Mech

class Session(Base):
    """Tracks active game rooms."""
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)  # e.g., "The Battle for Tukayyid"
    status: Mapped[str] = mapped_column(sa.String(20), default="active")  # active (lobby), in_progress, completed
    current_turn: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)  # 0 = not started

    # Relationship to get all mechs in this specific game session
    mechs: Mapped[List["SessionMech"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionMech(Base):
    """An instance of a Mech inside a specific game session."""
    __tablename__ = "session_mechs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(sa.ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    mech_id: Mapped[int] = mapped_column(sa.ForeignKey("mechs.id", ondelete="RESTRICT"), nullable=False)
    # Which side of the battle this unit fights for: "player" (friendly) or "enemy".
    team: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="player")

    # Database joins to travel between entities
    session: Mapped["Session"] = relationship(back_populates="mechs")
    master_mech: Mapped["Mech"] = relationship()
