"""LB-X Autocannon (cluster / shotgun mode) resolver.

An LB-X firing cluster (submunition) rounds behaves like a cluster weapon —
it fires ``num_shots`` one-damage pellets, rolls the Cluster Hits Table to see
how many connect, and scatters each pellet's damage across an independently
rolled hit location. Its signature difference is a **-1 to-hit modifier** in
cluster mode.

Because the scatter mechanics are identical to a missile rack, this reuses
:class:`~game.fire.cluster.ClusterShotResolver`'s hit resolution and only
overrides the to-hit adjustment.

(An LB-X can also fire a solid slug, which resolves as a normal single-location
shot — that path is handled by the standard resolver, not this class.)
"""

from game.fire.cluster import ClusterShotResolver


class LbxShotResolver(ClusterShotResolver):
    """Cluster-mode LB-X autocannon: cluster scatter with a -1 to-hit bonus."""

    # The to-hit bonus LB-X cluster rounds enjoy (negative = easier to hit).
    LBX_TO_HIT_MODIFIER = -1

    def _adjusted_target_number(self) -> int:
        """Apply the base per-band modifier, then the LB-X -1 cluster bonus."""
        return super()._adjusted_target_number() + self.LBX_TO_HIT_MODIFIER
