"""MRM (Medium-Range Missiles) shot resolver.

MRMs scatter like any missile rack, so the hit resolution is identical to a
cluster weapon. Their defining trait is a flat **+1 to-hit penalty** (cheap,
inaccurate missiles) and no Artemis fire-control benefit.

Because only the to-hit adjustment differs, this reuses
:class:`~game.fire.cluster.ClusterShotResolver` and overrides just that.
"""

from game.fire.cluster import ClusterShotResolver


class MrmShotResolver(ClusterShotResolver):
    """Cluster scatter with a +1 to-hit penalty."""

    # Positive = harder to hit.
    MRM_TO_HIT_MODIFIER = 1

    def _adjusted_target_number(self) -> int:
        """Apply the base per-band modifier, then the MRM +1 penalty."""
        return super()._adjusted_target_number() + self.MRM_TO_HIT_MODIFIER
