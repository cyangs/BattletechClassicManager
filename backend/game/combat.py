"""Combat resolution for game sessions.

This is a PLACEHOLDER implementation. Real BattleTech Classic to-hit
calculations (gunnery skill, range brackets, movement modifiers, terrain,
critical hits, heat effects, etc.) should replace the logic in
``CombatResolver.resolve_fire`` — the surrounding API contract can stay the
same so the frontend doesn't need to change when the real rules land.
"""

import random
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class WeaponShot:
    """One resolved weapon firing (a weapon mounted in count N fires N times)."""
    weapon: str
    location: str
    roll: int          # 2d6 to-hit roll
    target_number: int # number needed to hit
    hit: bool
    damage: int


class CombatResolver:
    """Resolves a mech firing a set of weapons.

    Placeholder rules:
      * Every shot rolls 2d6 against a flat gunnery target number of 7.
      * A hit deals the weapon's full damage; a miss deals 0.
      * Heat accrues whether or not the shot hits.
    """

    BASE_TARGET_NUMBER = 7

    def resolve_fire(self, attacker_name: str, weapons: List[dict]) -> dict:
        """weapons: list of {name, count, damage, heat, location} dicts."""
        shots: List[WeaponShot] = []
        total_damage = 0
        total_heat = 0

        for w in weapons:
            for _ in range(max(1, int(w.get("count", 1)))):
                roll = random.randint(1, 6) + random.randint(1, 6)
                hit = roll >= self.BASE_TARGET_NUMBER
                damage = int(w.get("damage") or 0) if hit else 0
                total_damage += damage
                total_heat += int(w.get("heat") or 0)
                shots.append(WeaponShot(
                    weapon=w.get("name", "Unknown"),
                    location=w.get("location", "—"),
                    roll=roll,
                    target_number=self.BASE_TARGET_NUMBER,
                    hit=hit,
                    damage=damage,
                ))

        hits = sum(1 for s in shots if s.hit)
        return {
            "attacker": attacker_name,
            "shots": [asdict(s) for s in shots],
            "hits": hits,
            "misses": len(shots) - hits,
            "total_damage": total_damage,
            "total_heat": total_heat,
        }
