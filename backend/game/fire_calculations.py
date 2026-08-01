"""Weapon-shot resolution: the rules that turn a fired weapon into a result.

Split out of :mod:`game.combat` because the shot-resolution logic (to-hit roll,
range-band modifiers, hit-location table lookup, cluster/variable damage) had
grown large enough to stand on its own.

:class:`WeaponShot` is a plain data record — just the fields describing one
resolved shot. :class:`FireCalculations` owns all the rules: give it a weapon
and the shot's context and :meth:`FireCalculations.resolve` returns a populated
:class:`WeaponShot`. :func:`serialize_shot` renders a shot as a JSON-safe dict
for the API response.
"""

import random
from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Optional

from game.cluster_hits_table import ClusterHitsTable
from game.tables import (
    RIGHT_SIDE_LOCATION_TABLE,
    FRONT_REAR_LOCATION_TABLE,
    LEFT_SIDE_LOCATION_TABLE,
)
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

# Which hit-location table a shot rolls on, keyed by the target's facing.
# Front/Rear is the default for any unrecognized facing.
_LOCATION_TABLE_BY_FACING = {
    "Left Side": LEFT_SIDE_LOCATION_TABLE,
    "Right Side": RIGHT_SIDE_LOCATION_TABLE,
    "Front/Rear": FRONT_REAR_LOCATION_TABLE,
}


def roll_2d6() -> int:
    """The all-important 2d6 roller."""
    return random.randint(1, 6) + random.randint(1, 6)


def roll_1d6() -> int:
    return random.randint(1, 6)


@dataclass
class DiceRollsResults:
    """Holds all raw dice results for a single weapon attack."""
    to_hit_1: int
    to_hit_2: int
    location_1: int | None = None
    location_2: int | None = None


@dataclass
class ClusterHit:
    """One cluster's worth of a cluster weapon's damage on a single location.

    e.g. an LRM 20 that lands 16 points with cluster_damage 5 produces four of
    these: 5/Left Arm, 5/Center Torso, 5/Right Leg, 1/Head (locations rolled
    independently per cluster).
    """
    location: str
    damage: int


@dataclass
class WeaponShot:
    """One resolved weapon firing — a plain data record with no logic.

    Produced by :class:`FireCalculations`. ``target_number`` of ``None`` means
    the target was out of the weapon's range (an automatic miss).
    """
    weapon: Weapon                          # The weapon that fired (source of stats)
    target_number: Optional[int]            # Number needed to hit (None = out of range)
    target_facing: str                      # The target's facing
    range_band: Optional[RangeBand] = None  # SHORT/MEDIUM/LONG bracket for this shot
    roll: int = 0                           # 2d6 to-hit total (0 when out of range)
    hit: bool = False
    hit_location: Optional[str] = "Torso"   # Single hit location; None for a cluster spread
    damage: int = 0                         # Damage dealt; 0 on a miss / out of range
    all_rolls: Optional[DiceRollsResults] = None  # Raw dice; None when out of range

    # Cluster weapons scatter their damage across several locations. For a
    # normal weapon these stay None and hit_location/damage describe the single
    # hit; for a cluster weapon cluster_hits holds the per-location breakdown
    # (and hit_location is None, damage is the total that landed).
    cluster_roll: Optional[int] = None            # 2d6 rolled on the cluster hits table
    cluster_hits_landed: Optional[int] = None     # total damage points that landed (table result)
    cluster_hits: Optional[list[ClusterHit]] = None


class FireCalculations:
    """Resolves one weapon shot into a :class:`WeaponShot`.

    Rolls the 2d6 to-hit, applies pulse-style range modifiers, decides the hit,
    rolls the hit location, and computes the (range-appropriate) damage.
    """

    def __init__(
        self,
        weapon: Weapon,
        target_number: Optional[int],
        target_facing: str,
        range_band: Optional[RangeBand] = None,
    ):
        self.weapon = weapon
        self.target_number = target_number
        self.target_facing = target_facing
        self.range_band = range_band

    def resolve(self) -> WeaponShot:
        """Roll out the shot and return the populated record."""
        # Out of range -> automatic miss. The roll/hit/damage fields keep their
        # defaults so callers inspecting the shot never see them unset.
        if self.target_number is None:
            return self._shot(hit_location="Target Out of Range")

        """ The all important to hit roll. Rolls a pair of 1D6 dice."""
        to_hit_1, to_hit_2 = roll_1d6(), roll_1d6()
        """ Sum of the pair of dice roll"""
        to_hit_roll = to_hit_1 + to_hit_2
        """ Store results for UI display"""
        all_rolls = DiceRollsResults(to_hit_1, to_hit_2)

        """ Applies any adjustments to the target number. Such as pulse weaponry"""
        target_number = self._adjusted_target_number()
        if to_hit_roll < target_number:
            return self._shot(
                target_number=target_number,
                roll=to_hit_roll,
                hit=False,
                hit_location="Miss",
                all_rolls=all_rolls,
            )

        """ Shot hit. Roll hit locations. """
        """ Weapon clusters. Roll clusters and hit locations. """
        if self.weapon.cluster:
            cluster_hit_roll = roll_1d6() + roll_1d6()
            cluster_hits = ClusterHitsTable.get_hits(
                max_cluster_size=self.weapon.num_shots,
                roll=cluster_hit_roll,
            )  # total missiles/pellets that hit

            # Damage dealt by a single missile/pellet.
            # SRM6: 12 damage / 6 shots = 2 dmg per missile
            # LRM20: 20 damage / 20 shots = 1 dmg per missile
            damage_per_missile = self.weapon.damage // self.weapon.num_shots

            # How many missiles are grouped together per location roll.
            # weapon.cluster_damage is expressed in DAMAGE, not missile count,
            # so convert it to a missile count by dividing out damage_per_missile.
            # LRM20: cluster_damage=5, damage_per_missile=1 -> 5 missiles per group
            # SRM6:  cluster_damage=2, damage_per_missile=2 -> 1 missile per group
            missiles_per_group = (self.weapon.cluster_damage or damage_per_missile) // damage_per_missile

            full_groups, remainder = divmod(cluster_hits, missiles_per_group)
            groups = [missiles_per_group] * full_groups
            if remainder:
                groups.append(remainder)

            """ Iterate through the groupings and roll location """
            group_hits: list[ClusterHit] = []
            for group_size in groups:
                """ simplify things and just roll 2D6; Dont track individual dice rolls """
                cluster_location_roll = roll_1d6() + roll_1d6()
                cluster_hit_location = self._hit_location(cluster_location_roll)
                group_hits.append(
                    ClusterHit(
                        location=cluster_hit_location,
                        damage=group_size * damage_per_missile,
                    )
                )

            """ Iterate through and the hits and sum up the total damage """
            total_damage = sum(hit.damage for hit in group_hits)

            """ A cluster spread has no single hit location; damage is the total that landed. """
            return self._shot(
                target_number=target_number,
                roll=to_hit_roll,
                hit=True,
                hit_location=None,
                damage=total_damage,
                all_rolls=all_rolls,
                cluster_roll=cluster_hit_roll,
                cluster_hits_landed=cluster_hits,
                cluster_hits=group_hits,
            )

        """ Weapon does NOT cluster. Just roll the location"""
        hit_location_roll_1 = roll_1d6()
        hit_location_roll_2 = roll_1d6()
        all_rolls.location_1 = hit_location_roll_1
        all_rolls.location_2 = hit_location_roll_2

        return self._shot(
            target_number=target_number,
            roll=to_hit_roll,
            hit=True,
            hit_location=self._hit_location(hit_location_roll_1 + hit_location_roll_2),
            damage=self._effective_damage(),
            all_rolls=all_rolls,
        )

    def _shot(self, **overrides) -> WeaponShot:
        """Build a WeaponShot carrying this shot's context plus the outcome.

        ``overrides`` win over the context defaults (e.g. the adjusted
        ``target_number`` on a resolved shot).
        """
        fields = {
            "weapon": self.weapon,
            "target_number": self.target_number,
            "target_facing": self.target_facing,
            "range_band": self.range_band,
        }
        fields.update(overrides)
        return WeaponShot(**fields)

    def _adjusted_target_number(self) -> int:
        """Apply the weapon's own per-band to-hit modifier, if any.

        A variable pulse laser, for example, stores -3/-2/-1 for
        short/medium/long. The (signed) modifier for this shot's band is added
        to the target number, so a negative value makes the shot easier to land.
        """
        modifier = self._weapon_range_modifier()
        if modifier is None:
            return self.target_number
        return self.target_number + modifier

    def _weapon_range_modifier(self) -> Optional[int]:
        """The weapon's stored to-hit modifier for this shot's range band."""
        return {
            RangeBand.SHORT: self.weapon.short_range_modifier,
            RangeBand.MEDIUM: self.weapon.medium_range_modifier,
            RangeBand.LONG: self.weapon.long_range_modifier,
        }.get(self.range_band)

    def _hit_location(self, location_roll: int) -> str:
        table = _LOCATION_TABLE_BY_FACING.get(self.target_facing, FRONT_REAR_LOCATION_TABLE)
        return table.get(location_roll, "Unknown Location")

    def _effective_damage(self) -> int:
        """Damage the weapon deals in this band (flat unless variable-damage)."""
        flat = int(self.weapon.damage or 0)
        if not self.weapon.variable_damage or self.range_band is None:
            return flat

        per_band = {
            RangeBand.SHORT: self.weapon.short_range_damage,
            RangeBand.MEDIUM: self.weapon.medium_range_damage,
            RangeBand.LONG: self.weapon.long_range_damage,
        }.get(self.range_band)
        # NULL per-band damage falls back to the flat damage value.
        return int(per_band) if per_band is not None else flat


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
        "all_rolls": asdict(shot.all_rolls) if shot.all_rolls else None,
        # Cluster breakdown (None for normal weapons).
        "cluster_roll": shot.cluster_roll,
        "cluster_hits_landed": shot.cluster_hits_landed,
        "cluster_hits": (
            [asdict(h) for h in shot.cluster_hits] if shot.cluster_hits is not None else None
        ),
    }
