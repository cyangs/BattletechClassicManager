"""Alpha Strike combat resolver — to-hit assembly + orchestration.

Parallel to Classic's :class:`game.combat.CombatResolver`: it turns the attack
inputs (pilot skill, movement, target TMM, distance) into a single to-hit
target number, picks the range bracket, then delegates the dice to the
lower-level :class:`~game.alpha_strike.calculator.AlphaStrikeResolver`.

Kept free of DB access — the API layer loads the cards and current
armor/structure and feeds them in, mirroring how ``CombatResolver`` is used.
"""

from typing import Optional

from game.alpha_strike.models import RangeBand
from game.alpha_strike.calculator import AlphaStrikeResolver


# To-hit modifier added per Alpha Strike range bracket.
RANGE_BAND_MODIFIER = {
    RangeBand.SHORT: 0,
    RangeBand.MEDIUM: 2,
    RangeBand.LONG: 4,
}


class AlphaStrikeCombatResolver:
    """Resolve one Alpha Strike attack from raw inputs into an AsAttackResult."""

    def __init__(
        self,
        attacker_card,
        target_card,
        pilot_skill: int,
        distance: int,
        damage_mode: str,
        target_armor: int,
        target_structure: int,
        attacker_movement_modifier: int = 0,
        additional_modifier: int = 0,
        attacker_name: Optional[str] = None,
        target_name: Optional[str] = None,
    ):
        self.attacker_card = attacker_card
        self.target_card = target_card
        self.pilot_skill = int(pilot_skill or 0)
        self.distance = int(distance or 0)
        self.damage_mode = damage_mode
        self.target_armor = int(target_armor or 0)
        self.target_structure = int(target_structure or 0)
        self.attacker_movement_modifier = int(attacker_movement_modifier or 0)
        self.additional_modifier = int(additional_modifier or 0)
        self.attacker_name = attacker_name
        self.target_name = target_name

    def resolve(self):
        band, range_modifier = self._range_bracket()

        # Out of range -> no valid target number (the lower resolver treats a
        # None target number as an automatic miss).
        if band is None:
            target_number = None
        else:
            # GATOR-equivalent: skill + attacker movement + target's TMM
            # + range bracket + any additional modifier.
            target_number = (
                self.pilot_skill
                + self.attacker_movement_modifier
                + int(getattr(self.target_card, "tmm", 0) or 0)
                + range_modifier
                + self.additional_modifier
            )

        return AlphaStrikeResolver(
            card=self.attacker_card,
            range_band=band,
            target_number=target_number,
            damage_mode=self.damage_mode,
            target_armor=self.target_armor,
            target_structure=self.target_structure,
            attacker_name=self.attacker_name,
            target_name=self.target_name,
        ).resolve()

    # Alpha Strike range brackets are FIXED game constants (inches), not
    # per-unit stats like Classic: Short 0-6, Medium 6-24, Long 24-42.
    SHORT_MAX = 6
    MEDIUM_MAX = 24
    LONG_MAX = 42

    def _range_bracket(self):
        """Map distance (inches) to (RangeBand, to-hit modifier).

        Returns ``(None, 0)`` when beyond long range (42").
        """
        if self.distance > self.LONG_MAX:
            return None, 0
        if self.distance > self.MEDIUM_MAX:
            return RangeBand.LONG, RANGE_BAND_MODIFIER[RangeBand.LONG]
        if self.distance > self.SHORT_MAX:
            return RangeBand.MEDIUM, RANGE_BAND_MODIFIER[RangeBand.MEDIUM]
        return RangeBand.SHORT, RANGE_BAND_MODIFIER[RangeBand.SHORT]
