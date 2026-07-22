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
from game.tables import RIGHT_SIDE_LOCATION_TABLE, FRONT_REAR_LOCATION_TABLE, LEFT_SIDE_LOCATION_TABLE

# 1. Create a dedicated class for the raw dice data
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
    weapon: str
    location: str
    target_number: int              # Number needed to hit
    target_facing: str              # The target's facing
    dice: DiceRollsResults          # Raw dice results for this shot
    damage: int = 0                 # Full weapon damage; zeroed on a miss

    # Automatically calculated fields (hidden from the initial constructor)
    roll: int = field(init=False)
    hit: bool = field(init=False)
    hit_location: str = field(init=False, default="Torso")

    def __post_init__(self) -> None:
        # Math is done automatically when the object is created.
        self.roll = self.dice.to_hit_1 + self.dice.to_hit_2
        self.hit = self.roll >= self.target_number

        if not self.hit:
            self.damage = 0
            self.hit_location = "Miss"
            return

        location_roll = self.dice.location_1 + self.dice.location_2

        # Take facing into account.
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

    Placeholder rules:
      * Every shot rolls 2d6 against a flat gunnery target number of 7.
      * A hit deals the weapon's full damage; a miss deals 0.
      * Heat accrues whether or not the shot hits.
    """

    BASE_TARGET_NUMBER = 7

    def resolve_fire(
        self,
        attacker_name: str,
        weapons: List[dict],
        target_name: str = None,
        target_facing: str = "Front/Rear",
        distance_modifier: int = 0,
        target_movement_modifier: int = 0,
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

        for w in weapons:
            for _ in range(max(1, int(w.get("count", 1)))):
                # The all important to-hit roll is here. #TOHIT
                first_to_hit_die = roll_1d6()
                second_to_hit_die = roll_1d6()

                """See if the weapon actually hits the target here"""
                total_die_roll = first_to_hit_die + second_to_hit_die
                hit = total_die_roll >= target_number
                """==============================================="""

                if hit:
                    first_hit_location_die = roll_1d6()
                    second_hit_location_die = roll_1d6()
                else:
                    first_hit_location_die = None
                    second_hit_location_die = None

                total_heat += int(w.get("heat") or 0)

                """Dice results container"""
                rolled_dice = DiceRollsResults(to_hit_1=first_to_hit_die,
                                               to_hit_2=second_to_hit_die,
                                               location_1=first_hit_location_die,
                                               location_2=second_hit_location_die)

                shot = WeaponShot(
                    weapon=w.get("name", "Unknown"),
                    location=w.get("location", "—"),
                    target_number=target_number,
                    dice=rolled_dice,
                    target_facing=target_facing,
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
