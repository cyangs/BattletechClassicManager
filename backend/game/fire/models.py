"""Data models and serialisation for weapon-shot resolution.

All plain data classes, enums, and the JSON serialiser live here so every
resolver subclass can import them without creating circular dependencies.
"""

from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Optional

from database.models.weapon import Weapon


class RangeBand(Enum):
    """The range band a shot falls into, used for variable-damage weapons."""
    SHORT = auto()
    MEDIUM = auto()
    LONG = auto()


# Standard BattleTech to-hit modifier added per range band.
RANGE_BAND_MODIFIER = {
    RangeBand.SHORT: 0,
    RangeBand.MEDIUM: 2,
    RangeBand.LONG: 4,
}


@dataclass
class DiceRollsResults:
    """Holds all raw dice results for a single weapon attack."""
    to_hit_1: int
    to_hit_2: int
    location_1: int | None = None
    location_2: int | None = None
    tac_reroll_1: int | None = None
    tac_reroll_2: int | None = None


@dataclass
class ClusterHit:
    """One cluster's worth of a cluster weapon's damage on a single location.

    e.g. an LRM 20 that lands 16 points with cluster_damage 5 produces four of
    these: 5/Left Arm, 5/Center Torso, 5/Right Leg, 1/Head (locations rolled
    independently per cluster).
    """
    location: str
    damage: int
    critical_hit: bool = False


@dataclass
class WeaponShot:
    """One resolved weapon firing — a plain data record with no logic.

    Produced by a :class:`~game.fire.base.BaseShotResolver` subclass.
    ``target_number`` of ``None`` means the target was out of the weapon's
    range (an automatic miss).
    """
    weapon: Weapon                                   # The weapon that fired (source of stats)
    target_number: Optional[int]                     # Number needed to hit (None = out of range)
    target_facing: str                               # The target's facing
    range_band: Optional[RangeBand] = None           # SHORT/MEDIUM/LONG bracket for this shot
    roll: int = 0                                    # 2d6 to-hit total (0 when out of range)
    hit: bool = False
    hit_location: Optional[str] = "Torso"            # Single hit location; None for a cluster spread
    damage: int = 0                                  # Damage dealt; 0 on a miss / out of range
    all_rolls: Optional[DiceRollsResults] = None     # Raw dice; None when out of range
    critical_hit: bool = False                       # if the hit was a through armor crit or not.

    # Cluster weapons scatter their damage across several locations. For a
    # normal weapon these stay None and hit_location/damage describe the single
    # hit; for a cluster weapon cluster_hits holds the per-location breakdown
    # (and hit_location is None, damage is the total that landed).
    cluster_roll: Optional[int] = None            # 2d6 rolled on the cluster hits table
    cluster_hits_landed: Optional[int] = None     # total damage points that landed (table result)
    cluster_hits: Optional[list[ClusterHit]] = None


def serialize_shot(shot: WeaponShot) -> dict:
    """JSON-safe view of a shot for the API response.

    ``weapon`` is a SQLAlchemy ORM object and ``range_band`` is an enum — neither
    is JSON serializable, so this flattens them to a display name and a band
    label the frontend can render directly.
    """
    return {
        "weapon": (shot.weapon.full_name or shot.weapon.name) if shot.weapon else None,
        "target_number": shot.target_number,
        "target_facing": shot.target_facing,
        "range_band": shot.range_band.name if shot.range_band else None,
        "roll": shot.roll,
        "hit": shot.hit,
        "hit_location": shot.hit_location,
        "damage": shot.damage,
        "critical_hit": shot.critical_hit,
        "all_rolls": asdict(shot.all_rolls) if shot.all_rolls else None,
        # Cluster breakdown (None for normal weapons).
        "cluster_roll": shot.cluster_roll,
        "cluster_hits_landed": shot.cluster_hits_landed,
        "cluster_hits": (
            [asdict(h) for h in shot.cluster_hits] if shot.cluster_hits is not None else None
        ),
    }
