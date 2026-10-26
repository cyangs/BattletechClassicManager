"""Alpha Strike attack resolver.

Pure logic: given an attacker's AS card, the range bracket, an already-computed
to-hit target number, the damage mode, and the target's current armor/structure,
resolve one attack into an :class:`AsAttackResult`.

The to-hit *number* is computed by the caller (it knows pilot skill, movement,
target TMM, range mod) — mirroring how the Classic resolvers receive their
target number. This keeps the calculator free of game-state lookups and fully
unit-testable.
"""

import random
from typing import Optional

from game.alpha_strike.models import RangeBand, AsAttackResult


def roll_2d6() -> int:
    return random.randint(1, 6) + random.randint(1, 6)


def roll_2d6_pair() -> tuple[int, int]:
    """Roll 2d6 and return the individual dice (not just the sum)."""
    return random.randint(1, 6), random.randint(1, 6)


class AlphaStrikeResolver:
    """Resolves one Alpha Strike attack into an :class:`AsAttackResult`."""

    def __init__(
        self,
        card,
        range_band: Optional[RangeBand],
        target_number: Optional[int],
        damage_mode: str,                 # "standard" | "variable"
        target_armor: int,
        target_structure: int,
        attacker_name: Optional[str] = None,
        target_name: Optional[str] = None,
    ):
        self.card = card
        self.range_band = range_band
        self.target_number = target_number
        self.damage_mode = damage_mode
        self.target_armor = int(target_armor or 0)
        self.target_structure = int(target_structure or 0)
        self.attacker_name = attacker_name
        self.target_name = target_name

    def resolve(self) -> AsAttackResult:
        bracket_damage = self._bracket_damage()

        # Out of range -> automatic miss (no dice, no damage).
        if self.target_number is None or self.range_band is None:
            return self._result(bracket_damage=bracket_damage, damage_dealt=0,
                                 hit=False, roll_pairs=[])

        if self.damage_mode == "variable":
            # One 2d6 per point of bracket damage, each vs the same target number.
            roll_pairs = [roll_2d6_pair() for _ in range(bracket_damage)]
            damage_dealt = sum(1 for d1, d2 in roll_pairs if d1 + d2 >= self.target_number)
            hit = damage_dealt > 0
        else:  # standard (all-or-nothing): a single 2d6.
            roll_pairs = [roll_2d6_pair()]
            d1, d2 = roll_pairs[0]
            hit = d1 + d2 >= self.target_number
            damage_dealt = bracket_damage if hit else 0

        return self._result(bracket_damage=bracket_damage,
                            damage_dealt=damage_dealt, hit=hit, roll_pairs=roll_pairs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _bracket_damage(self) -> int:
        """The attacker's damage for this shot's range bracket."""
        return {
            RangeBand.SHORT: self.card.damage_short,
            RangeBand.MEDIUM: self.card.damage_medium,
            RangeBand.LONG: self.card.damage_long,
        }.get(self.range_band, 0) or 0

    def _result(self, *, bracket_damage: int, damage_dealt: int, hit: bool, roll_pairs) -> AsAttackResult:
        """Apply damage to armor then structure and package the result.

        ``roll_pairs`` is a list of (d1, d2) tuples — one per 2d6 rolled.
        ``rolls`` (the per-roll totals) is derived from them for convenience.
        """
        armor_before = self.target_armor
        structure_before = self.target_structure

        remaining = damage_dealt
        armor_after = max(0, armor_before - remaining)
        remaining -= (armor_before - armor_after)           # damage absorbed by armor
        structure_after = max(0, structure_before - remaining)

        return AsAttackResult(
            attacker=self.attacker_name,
            target=self.target_name,
            range_band=self.range_band,
            target_number=self.target_number,
            mode=self.damage_mode,
            bracket_damage=bracket_damage,
            damage_dealt=damage_dealt,
            hit=hit,
            roll_pairs=[list(p) for p in roll_pairs],
            rolls=[d1 + d2 for d1, d2 in roll_pairs],
            target_armor_before=armor_before,
            target_armor_after=armor_after,
            target_structure_before=structure_before,
            target_structure_after=structure_after,
        )
