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
from game.tables import RIGHT_SIDE_LOCATION_TABLE, FRONT_REAR_LOCATION_TABLE, LEFT_SIDE_LOCATION_TABLE

from backend.database.dao import weapon_repository
from backend.database.dao.weapon_repository import WeaponRepository
from backend.database.models.weapon import Weapon

"""Used to define the range band of the hit for damage calculations"""
class RangeBand(Enum):
    SHORT = auto()
    MEDIUM = auto()
    LONG = auto()


@dataclass
class DiceRollsResults:
    """Holds all raw dice results for a single weapon attack."""
    to_hit_1: int
    to_hit_2: int
    location_1: int | None = None
    location_2: int | None = None

@dataclass
class WeaponShot:
    """One resolved weapon firing (a weapon mounted in count N fires N times)."""
    weapon: Weapon
    location: str
    target_number: int              # Number needed to hit
    target_facing: str              # The target's facing
    range_band: None                # Range band for damage calculation
    damage: int = 0                 # Full weapon damage; zeroed on a miss

    # Automatically calculated fields (hidden from the initial constructor)
    roll: int = field(init=False)
    hit: bool = field(init=False)
    hit_location: str = field(init=False, default="Torso")

    # Math is done automatically when the object is created.
    def __post_init__(self) -> None:
        """Record miss if out of range"""
        if self.target_number is None:
            self.damage = 0
            self.hit_location = "Target Out of Range"
            return

        """Roll both sets of dice for visibility"""
        first_to_hit_die = roll_1d6()
        second_to_hit_die = roll_1d6()

        """Dice results container"""
        dice_record = DiceRollsResults(to_hit_1=first_to_hit_die,
                                       to_hit_2=second_to_hit_die)

        """See if the weapon actually hits the target here"""
        """==============================================="""
        self.roll = first_to_hit_die + second_to_hit_die
        self.hit = self.roll >= self.target_number
        """==============================================="""

        if not self.hit:
            self.damage = 0
            self.hit_location = "Miss"
            return

        if hit:
            first_hit_location_die = roll_1d6()
            second_hit_location_die = roll_1d6()
            dice_record.location_1 = first_hit_location_die
            dice_record.location_2 = second_hit_location_die

            """Location roll when hit"""
            location_roll = first_hit_location_die + second_hit_location_die

            # Take facing into account.
            if self.target_facing == "Left Side":
                self.hit_location = LEFT_SIDE_LOCATION_TABLE.get(location_roll, "Unknown Location")
            elif self.target_facing == "Right Side":
                self.hit_location = RIGHT_SIDE_LOCATION_TABLE.get(location_roll, "Unknown Location")
            else:
                self.hit_location = FRONT_REAR_LOCATION_TABLE.get(location_roll, "Unknown Location")

            """ TODO RANGE CHECK FOR DAMAGE"""


""" The all important 2d6 roller"""
def roll_2d6():
    return random.randint(1, 6) + random.randint(1, 6)

def roll_1d6():
    return random.randint(1, 6)


class CombatResolver:
    """Resolves a mech firing a set of weapons.

    Placeholder rules:
      * Every shot rolls 2d6 against a flat gunnery target number of 7.
      * A hit deals the weapon's full damage; a miss deals 0.
      * Heat accrues whether or not the shot hits.
    """

    BASE_TARGET_NUMBER = 7

    def resolve_fire(
        self,
        attacker_name: str,
        weapons: List[Weapon],
        target_name: str = None,
        target_facing: str = "Front/Rear",
        distance_modifier: int = 0,
        target_movement_modifier: int = 0,
        intervening_terrain: int = 0,
        partial_cover: bool = False,
    ) -> dict:
        """weapons: list of {name, count, damage, heat, location} dicts.

        target_name: display name of the enemy mech being fired upon (optional).
        facing: which arc the target is presenting ("Left Side", "Front/Rear",
            "Right Side"). Passed through for display / future hit-location rules.
        target_movement_modifier: to-hit penalty from the target's movement,
            added on top of the base gunnery target number.
        """
        shots: List[WeaponShot] = []
        total_damage = 0
        total_heat = 0

        target_number = self.BASE_TARGET_NUMBER + int(target_movement_modifier or 0)

        # iterate through list of mech weapons firing
        for weapon in weapons:
            db_weapon = WeaponRepository.fetch_weapon_by_name(name = weapon.full_name)

            for _ in range(max(1, int(db_weapon.get("count", 1)))):
                range_band = None

                """ Check if the weapon can reach out to target range"""
                if distance_modifier > db_weapon.long_range:
                    target_number = None

                """Long range shot"""
                if db_weapon.long_range >= distance_modifier >= db_weapon.medium_range:
                    target_number = target_number + 4
                    if weapon.variable_damage:
                        range_band = RangeBand.LONG

                """Medium range shot"""
                if db_weapon.medium_range >= distance_modifier >= db_weapon.short_range:
                    target_number = target_number + 2
                    if weapon.variable_damage:
                        range_band = RangeBand.MEDIUM

                """ Short range has no modifier"""
                if db_weapon.short_range >= distance_modifier and weapon.variable_damage:
                    range_band = RangeBand.SHORT

                """ TODO: Calculate minimum range issues here"""

                total_heat += int(w.get("heat") or 0)

                shot = WeaponShot(
                    weapon=db_weapon.get("name", "Unknown"),
                    location=w.get("location", "—"),
                    target_number=target_number,
                    target_facing=target_facing,
                    range_band=range_band,
                    damage=int(w.get("damage") or 0),
                )
                # WeaponShot zeroes damage on a miss in __post_init__.
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
        }
