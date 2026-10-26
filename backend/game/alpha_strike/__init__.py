"""Public surface of the game.alpha_strike package.

    from game.alpha_strike import (
        RangeBand, AsAttackResult, serialize_as_attack,
        AlphaStrikeResolver, roll_2d6,
    )
"""

from game.alpha_strike.models import (
    RangeBand,
    AsAttackResult,
    serialize_as_attack,
)
from game.alpha_strike.calculator import AlphaStrikeResolver, roll_2d6
from game.alpha_strike.combat import AlphaStrikeCombatResolver, RANGE_BAND_MODIFIER

__all__ = [
    "RangeBand",
    "AsAttackResult",
    "serialize_as_attack",
    "AlphaStrikeResolver",
    "AlphaStrikeCombatResolver",
    "RANGE_BAND_MODIFIER",
    "roll_2d6",
]
