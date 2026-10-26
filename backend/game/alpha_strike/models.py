"""Data models and serialisation for Alpha Strike attack resolution.

Separate from the Classic :mod:`game.fire` models — Alpha Strike has its own,
much simpler, shape: bracket damage + flat armor/structure, no hit locations.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List


class RangeBand(Enum):
    """Which range bracket an Alpha Strike attack falls into."""
    SHORT = auto()
    MEDIUM = auto()
    LONG = auto()


@dataclass
class AsAttackResult:
    """One resolved Alpha Strike attack — a plain data record.

    ``target_number`` of ``None`` means the attack was out of range (an
    automatic miss). ``rolls`` holds the 2d6 total(s): one entry in standard
    mode, one per point of bracket damage in variable mode, empty when out of
    range or when the bracket deals 0.
    """
    attacker: Optional[str]
    target: Optional[str]
    range_band: Optional[RangeBand]
    target_number: Optional[int]
    mode: str                                   # "standard" | "variable"
    bracket_damage: int                         # max possible this attack
    damage_dealt: int                           # actually applied to the target
    hit: bool
    rolls: List[int] = field(default_factory=list)          # per-roll 2d6 totals
    roll_pairs: List[list] = field(default_factory=list)    # per-roll [d1, d2] dice

    # Target armor/structure before and after this attack's damage.
    target_armor_before: Optional[int] = None
    target_armor_after: Optional[int] = None
    target_structure_before: Optional[int] = None
    target_structure_after: Optional[int] = None


def serialize_as_attack(result: AsAttackResult) -> dict:
    """JSON-safe view of an Alpha Strike attack for the API / event payload."""
    return {
        "attacker": result.attacker,
        "target": result.target,
        "range_band": result.range_band.name if result.range_band else None,
        "target_number": result.target_number,
        "mode": result.mode,
        "bracket_damage": result.bracket_damage,
        "damage_dealt": result.damage_dealt,
        "hit": result.hit,
        "rolls": result.rolls,
        "roll_pairs": result.roll_pairs,
        "target_armor_before": result.target_armor_before,
        "target_armor_after": result.target_armor_after,
        "target_structure_before": result.target_structure_before,
        "target_structure_after": result.target_structure_after,
    }
