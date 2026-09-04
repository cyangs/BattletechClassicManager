"""Public surface of the game.fire package.

Import from here rather than from the individual sub-modules:

    from game.fire import (
        RangeBand, RANGE_BAND_MODIFIER,
        WeaponShot, ClusterHit, DiceRollsResults,
        serialize_shot,
        BaseShotResolver,
        StandardShotResolver, ClusterShotResolver, UltraShotResolver,
        roll_1d6, roll_2d6,
    )
"""

from game.fire.models import (
    RangeBand,
    RANGE_BAND_MODIFIER,
    DiceRollsResults,
    ClusterHit,
    WeaponShot,
    serialize_shot,
)
from game.fire.base import (
    BaseShotResolver,
    roll_1d6,
    roll_2d6,
)
from game.fire.standard import StandardShotResolver
from game.fire.cluster import ClusterShotResolver
from game.fire.ultra import UltraShotResolver

__all__ = [
    # Models & enums
    "RangeBand",
    "RANGE_BAND_MODIFIER",
    "DiceRollsResults",
    "ClusterHit",
    "WeaponShot",
    "serialize_shot",
    # Base
    "BaseShotResolver",
    # Resolvers
    "StandardShotResolver",
    "ClusterShotResolver",
    "UltraShotResolver",
    # Dice helpers
    "roll_1d6",
    "roll_2d6",
]
