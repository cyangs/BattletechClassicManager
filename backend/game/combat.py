"""Combat resolution for game sessions.

This is a PLACEHOLDER implementation. Real BattleTech Classic to-hit
calculations (gunnery skill, range brackets, movement modifiers, terrain,
critical hits, heat effects, etc.) should replace the logic in
``CombatResolver.resolve_fire`` — the surrounding API contract can stay the
same so the frontend doesn't need to change when the real rules land.
"""

import random
from dataclasses import dataclass, asdict, field
from typing import List
from enum import Enum, auto
from typing import List, Optional
from game.tables import RIGHT_SIDE_LOCATION_TABLE, FRONT_REAR_LOCATION_TABLE, LEFT_SIDE_LOCATION_TABLE
from database.dao.weapon_repository import WeaponRepository


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


@dataclass
class WeaponShot:
    """One resolved weapon firing.

    ``target_number`` of ``None`` means the target is out of the weapon's
    range, which resolves to an automatic miss.
    """
    weapon: str                             # Display name of the weapon
    target_number: Optional[int]            # Number needed to hit (None = out of range)
    target_facing: str                      # The target's facing
    range_band: Optional[str] = None        # "SHORT"/"MEDIUM"/"LONG" for display
    damage: int = 0                         # Full weapon damage; zeroed on a miss

    # Automatically calculated fields (hidden from the initial constructor).
    roll: int = field(init=False, default=0)
    hit: bool = field(init=False, default=False)
    hit_location: str = field(init=False, default="Torso")
    # Raw 2d6 to-hit (and, on a hit, location) rolls. Declared as a field so it
    # is included when the shot is serialized via ``asdict``. ``None`` when the
    # target is out of range and no roll is made.
    all_rolls: Optional[DiceRollsResults] = field(init=False, default=None)

    def __post_init__(self) -> None:
        # Out of range -> automatic miss. roll/hit keep their defaults so
        # downstream code that inspects ``shot.hit`` never sees an unset field.
        if self.target_number is None:
            self.damage = 0
            self.hit_location = "Target Out of Range"
            return

        """The all-important 2d6 to-hit roll."""
        first_1d6_roll = roll_1d6()
        second_1d6_roll = roll_1d6()

        self.roll = first_1d6_roll + second_1d6_roll
        self.hit = self.roll >= self.target_number

        """ Store individual hit rolls for tracking purposes"""
        self.all_rolls = DiceRollsResults(first_1d6_roll, second_1d6_roll)

        if not self.hit:
            self.damage = 0
            self.hit_location = "Miss"
            return

        """Roll 2d6 for the hit location, honouring the target's facing."""
        first_1d6_location_roll = roll_1d6()
        second_1d6_location_roll = roll_1d6()

        location_roll = first_1d6_location_roll + second_1d6_location_roll

        """ Store individual location hit rolls for tracking purposes"""
        self.all_rolls.location_1 = first_1d6_location_roll
        self.all_rolls.location_2 = second_1d6_location_roll


        if self.target_facing == "Left Side":
            self.hit_location = LEFT_SIDE_LOCATION_TABLE.get(location_roll, "Unknown Location")
        elif self.target_facing == "Right Side":
            self.hit_location = RIGHT_SIDE_LOCATION_TABLE.get(location_roll, "Unknown Location")
        else:
            self.hit_location = FRONT_REAR_LOCATION_TABLE.get(location_roll, "Unknown Location")


""" The all important 2d6 roller"""
def roll_2d6():
    return random.randint(1, 6) + random.randint(1, 6)

def roll_1d6():
    return random.randint(1, 6)


class CombatResolver:
    """Resolves a mech firing a set of weapons.

    The resolver is given a list of weapon *names*; it looks each one up in the
    database (via :class:`WeaponRepository`) and resolves the shot using the
    stats on the found weapon record — the database is the source of truth for
    damage, heat, range brackets and the variable-damage / cluster flags.

    Placeholder rules:
      * To-hit target number = pilot gunnery skill + movement + terrain +
        cover + the weapon's range-bracket modifier.
      * A shot beyond the weapon's long range is an automatic miss.
      * A hit deals the weapon's (range-appropriate) damage; a miss deals 0.
      * Heat accrues whether or not the shot hits.
    """

    # Simplified partial-cover to-hit penalty.
    PARTIAL_COVER_MODIFIER = 1

    def __init__(self, weapon_repository: WeaponRepository):
        self.weapon_repository = weapon_repository

    def resolve_fire(
        self,
        attacker_name: str,
        weapon_names: List[str],
        pilot_gunnery_skill: int,
        target_name: str = None,
        target_facing: str = "Front/Rear",
        distance_modifier: int = 0,
        additional_modifier: int = 0,
        target_movement_modifier: int = 0,
        self_movement_modifier: int = 0,
        partial_cover: bool = False,
    ) -> dict:
        """Resolve a mech firing its selected weapons.

        weapon_names: names of the weapons firing (as stored in
            ``weapons_master.name``). A weapon firing more than once appears in
            the list once per shot. Each name is looked up in the database and
            resolved using the found record's stats.
        pilot_gunnery_skill: the attacker's gunnery skill — the base to-hit number.
        target_name: display name of the enemy mech being fired upon (optional).
        target_facing: which arc the target is presenting ("Left Side",
            "Front/Rear", "Right Side").
        distance_modifier: range to the target, in hexes.
        target_movement_modifier: to-hit penalty from the target's movement.
        intervening_terrain: to-hit penalty from terrain between attacker/target.
        partial_cover: whether the target is partially obscured.
        """
        shots: List[WeaponShot] = []
        unresolved: List[str] = []
        total_damage = 0
        total_heat = 0

        """Modifiers shared by every shot this attack. The per-weapon range
           bracket is added on top of this, per shot, below.
           
           This the basic modifier calculation, following GATOR
           
           1. (G) It takes the gunnery skill as the base.
           2. (A) Adds the attacker movement modifier
           3. (T) Adds the target movement modifier
           4. (O) adds any additional modifiers
                  - See below for range modifier addition
           """
        base_modifiers = (
            int(pilot_gunnery_skill or 0)
            + int(target_movement_modifier or 0)
            + int(self_movement_modifier or 0)
            + int(additional_modifier or 0)
        )

        distance = int(distance_modifier or 0)
        lookup_cache: dict = {}

        for name in weapon_names:
            """Look the weapon up in the database (cached)"""
            if name not in lookup_cache:
                lookup_cache[name] = self.weapon_repository.fetch_weapon_by_name(name)
            db_weapon = lookup_cache[name]

            if db_weapon is None:
                # Unknown weapon name — record it rather than silently dropping.
                unresolved.append(name)
                continue

            band, range_modifier = self._range_bracket(distance, db_weapon)
            # Beyond long range -> no valid target number (auto miss).
            """ 5. (R) range modifier is added """
            target_number = None if band is None else base_modifiers + range_modifier
            damage = self._effective_damage(db_weapon, band)

            # Heat accrues whether or not the shot lands (or is in range).
            total_heat += int(db_weapon.heat or 0)

            shot = WeaponShot(
                weapon=db_weapon.full_name or db_weapon.name,
                target_number=target_number,
                target_facing=target_facing,
                range_band=band.name if band is not None else None,
                damage=damage,
            )
            # WeaponShot zeroes damage on a miss / out-of-range in __post_init__.
            total_damage += shot.damage
            shots.append(shot)

        hits = sum(1 for s in shots if s.hit)
        return {
            "attacker": attacker_name,
            "target": target_name,
            "target_movement_modifier": int(target_movement_modifier or 0),
            "shots": [asdict(s) for s in shots],
            "hits": hits,
            "misses": len(shots) - hits,
            "total_damage": total_damage,
            "total_heat": total_heat,
            "unresolved_weapons": unresolved,
        }

    def _range_bracket(self, distance: int, weapon):
        """Return ``(RangeBand, to_hit_modifier)`` for the distance to target.

        Returns ``(None, 0)`` when the target is beyond the weapon's long range.
        # TODO: apply a minimum-range penalty when distance < minimum_range.
        """
        short = int(weapon.short_range or 0)
        medium = int(weapon.medium_range or 0)
        long_ = int(weapon.long_range or 0)

        if distance > long_:
            return None, 0
        if distance > medium:
            return RangeBand.LONG, RANGE_BAND_MODIFIER[RangeBand.LONG]
        if distance > short:
            return RangeBand.MEDIUM, RANGE_BAND_MODIFIER[RangeBand.MEDIUM]
        return RangeBand.SHORT, RANGE_BAND_MODIFIER[RangeBand.SHORT]

    def _effective_damage(self, weapon, band) -> int:
        """Damage the weapon deals in this band (flat damage unless variable)."""
        flat = int(weapon.damage or 0)
        if not weapon.variable_damage or band is None:
            return flat

        per_band = {
            RangeBand.SHORT: weapon.short_range_damage,
            RangeBand.MEDIUM: weapon.medium_range_damage,
            RangeBand.LONG: weapon.long_range_damage,
        }.get(band)
        # NULL per-band damage falls back to the flat damage value.
        return int(per_band) if per_band is not None else flat
