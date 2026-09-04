"""Backward-compatibility shim for game.fire_calculations.

All logic has moved to the :mod:`game.fire` package.  This module re-exports
the full previous public surface so any existing import of the form::

    from game.fire_calculations import WeaponShot, FireCalculations, ...

continues to work without modification.

``FireCalculations`` is aliased to :class:`~game.fire.base.BaseShotResolver`
for import compatibility; new code should instantiate the specific resolver
subclass directly via :mod:`game.fire`.
"""

from game.fire import (                      # noqa: F401  (re-export)
    RangeBand,
    RANGE_BAND_MODIFIER,
    DiceRollsResults,
    ClusterHit,
    WeaponShot,
    serialize_shot,
    BaseShotResolver,
    StandardShotResolver,
    ClusterShotResolver,
    UltraShotResolver,
    roll_1d6,
    roll_2d6,
)

# Legacy alias — old code that imported FireCalculations directly will still
# resolve the name, though it can no longer be instantiated directly
# (BaseShotResolver is abstract).  Callers should migrate to the concrete
# resolver classes in game.fire.
FireCalculations = BaseShotResolver
