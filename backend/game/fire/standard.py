"""Standard (non-cluster) weapon shot resolver.

Handles any weapon that deals a single block of damage to one location:
lasers, PPCs, standard autocannons, non-cluster SRMs, etc.  Variable-damage
weapons (e.g. pulse lasers with per-band damage values) are also handled here
via :meth:`~game.fire.base.BaseShotResolver._effective_damage`.
"""

from game.fire.base import BaseShotResolver
from game.fire.models import DiceRollsResults, WeaponShot


class StandardShotResolver(BaseShotResolver):
    """Resolves a single-location, single-damage-block weapon hit."""

    def _resolve_hit(
        self,
        target_number: int,
        to_hit_roll: int,
        all_rolls: DiceRollsResults,
    ) -> WeaponShot:
        """Resolve a non-cluster weapon hit: roll one location and apply TAC if needed."""
        """ Weapon does NOT cluster. Just roll the location"""
        hit_location_roll, critical_hit, tac_rolls = self._resolve_location_with_tac()
        roll_1, roll_2 = tac_rolls[:2]
        all_rolls.location_1 = roll_1
        all_rolls.location_2 = roll_2

        """ Through armor critical resolution — reroll dice are stored for display """
        if critical_hit and len(tac_rolls) == 4:
            all_rolls.tac_reroll_1 = tac_rolls[2]
            all_rolls.tac_reroll_2 = tac_rolls[3]

        return self._shot(
            target_number=target_number,
            roll=to_hit_roll,
            hit=True,
            hit_location=self._hit_location(hit_location_roll),
            damage=self._effective_damage(),
            all_rolls=all_rolls,
            critical_hit=critical_hit,
        )
