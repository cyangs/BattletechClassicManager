"""Combat resolution for game sessions.

This is a PLACEHOLDER implementation. Real BattleTech Classic to-hit
calculations (gunnery skill, range brackets, movement modifiers, terrain,
critical hits, heat effects, etc.) should replace the logic in
``CombatResolver.resolve_fire`` — the surrounding API contract can stay the
same so the frontend doesn't need to change when the real rules land.
"""

from typing import List

from database.dao.weapon_repository import WeaponRepository
# WeaponShot and its supporting types live in their own module now; re-exported
# here so existing ``from game.combat import WeaponShot`` style imports keep
# working.
from game.fire_calculations import (
    RangeBand,
    RANGE_BAND_MODIFIER,
    DiceRollsResults,
    ClusterHit,
    WeaponShot,
    FireCalculations,
    serialize_shot,
    roll_1d6,
    roll_2d6,
)
from models import SessionMech


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

    def __init__(self, weapon_repository: WeaponRepository):
        self.weapon_repository = weapon_repository

    def resolve_fire(
        self,
        unit: SessionMech,
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

        ## TODO iterate through unit.attachments and see if anything has a to_hit_modifier


        for name in weapon_names:
            """Look the weapon up in the database (cached)"""
            if name not in lookup_cache:
                lookup_cache[name] = self.weapon_repository.fetch_weapon_by_name(name)
            db_weapon = lookup_cache[name]

            if db_weapon is None:
                # Unknown weapon name — record it rather than silently dropping.
                unresolved.append(name)
                continue

            """ 5. (R) range modifier is added """
            """ Beyond long range -> no valid target number (auto miss)."""
            band, range_modifier = self._range_bracket(distance, db_weapon)
            target_number = None if band is None else base_modifiers + range_modifier

            # Heat accrues whether the shot lands (or is in range).
            total_heat += int(db_weapon.heat or 0)

            shot = FireCalculations(
                weapon=db_weapon,
                target_number=target_number,
                target_facing=target_facing,
                range_band=band,
            ).resolve()

            # FireCalculations zeroes damage on a miss / out-of-range.
            total_damage += shot.damage
            shots.append(shot)

        hits = sum(1 for s in shots if s.hit)
        return {
            "attacker": unit.master_mech.name,
            "target": target_name,
            "target_movement_modifier": int(target_movement_modifier or 0),
            "shots": [serialize_shot(s) for s in shots],
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


