"""Heavy Laser shot resolver.

Heavy Lasers (Clan Heavy Small/Medium/Large) deal more damage and run far
hotter than standard lasers, but are less accurate: they carry a **+1 to-hit
penalty**. A hit lands on a single rolled location like any laser, so this
reuses :class:`~game.fire.standard.StandardShotResolver` and only overrides the
to-hit adjustment (mirroring how MRM adds +1 and LB-X subtracts 1).

The extra damage/heat are data on the weapon row (``damage`` / ``heat``); only
the accuracy penalty needs resolver logic.
"""

from game.fire.standard import StandardShotResolver


class HeavyLaserShotResolver(StandardShotResolver):
    """Single-location laser hit with a +1 to-hit penalty."""

    # Positive = harder to hit.
    HEAVY_LASER_TO_HIT_MODIFIER = 1

    def _adjusted_target_number(self) -> int:
        """Apply the base per-band modifier, then the heavy-laser +1 penalty."""
        return super()._adjusted_target_number() + self.HEAVY_LASER_TO_HIT_MODIFIER
