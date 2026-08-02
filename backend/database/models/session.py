from typing import List, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base
from datetime import datetime, timezone

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
    created_on: Mapped[DateTime] = mapped_column(sa.DateTime, nullable=False, default=datetime.now(timezone.utc))

    # Relationship to get all mechs in this specific game session
    mechs: Mapped[List["SessionMech"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    # Chronological log of things that have happened in the session (e.g. fires).
    events: Mapped[List["SessionEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="SessionEvent.id"
    )


class SessionMech(Base):
    """An instance of a Mech inside a specific game session."""
    __tablename__ = "session_mechs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(sa.ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    mech_id: Mapped[int] = mapped_column(sa.ForeignKey("mechs.id", ondelete="RESTRICT"), nullable=False)
    # Which side of the battle this unit fights for: "player" (friendly) or "enemy".
    team: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="player")
    # Pilot assigned to this unit for the duration of the session.
    pilot_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    # Gunnery skill (0 best, 8 worst); the base to-hit number when this unit fires.
    pilot_gunnery_skill: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=4)

    # Database joins to travel between entities
    session: Mapped["Session"] = relationship(back_populates="mechs")
    master_mech: Mapped["Mech"] = relationship()
    # Per-weapon disable flags for this unit, carried for the whole session.
    weapon_states: Mapped[List["SessionWeaponState"]] = relationship(
        back_populates="session_mech", cascade="all, delete-orphan"
    )


class SessionEvent(Base):
    """A single logged event in a session's history (currently: weapon fires).

    ``payload`` holds the full, opaque result of the action (for a fire, the
    resolved shots and dice rolls) so the history view can render exactly what
    happened without recomputing anything.
    """
    __tablename__ = "session_events"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        sa.ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    turn: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    event_type: Mapped[str] = mapped_column(sa.String(30), nullable=False, default="fire")
    # The firing unit (nullable so history survives if the unit is later removed).
    session_mech_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("session_mechs.id", ondelete="SET NULL"), nullable=True
    )
    attacker: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    target: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    payload: Mapped[dict] = mapped_column(sa.JSON, nullable=False, default=dict)

    session: Mapped["Session"] = relationship(back_populates="events")


class SessionWeaponState(Base):
    """Tracks whether an individual weapon instance is disabled for a unit.

    ``weapon_key`` matches the frontend's per-instance key ("<link_id>#<index>")
    so a single mounted weapon of count N can be disabled instance-by-instance.
    A row exists only while the weapon is disabled.
    """
    __tablename__ = "session_weapon_states"
    __table_args__ = (
        sa.UniqueConstraint("session_mech_id", "weapon_key", name="uq_session_weapon_instance"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_mech_id: Mapped[int] = mapped_column(
        sa.ForeignKey("session_mechs.id", ondelete="CASCADE"), nullable=False
    )
    weapon_key: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    disabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)

    session_mech: Mapped["SessionMech"] = relationship(back_populates="weapon_states")
