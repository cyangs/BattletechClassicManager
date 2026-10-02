"""HAG (Hyper-Assault Gauss) shot resolver.

A HAG scatters its submunitions exactly like a cluster weapon, so it reuses
:class:`~game.fire.cluster.ClusterShotResolver`'s hit resolution. Its defining
rule is a **range-based modifier to the Cluster Hits Table roll** (not the
to-hit roll):

  * Short range:  +2   (more submunitions connect up close)
  * Medium range:  0
  * Long range:   -2   (fewer connect at distance)

HAG/20, HAG/30 and HAG/40 differ only in data (num_shots / cluster size), so a
single resolver covers all three.
"""

from game.fire.cluster import ClusterShotResolver


class HagShotResolver(ClusterShotResolver):
    """Cluster scatter with a HAG's range-based cluster-roll modifier."""

    def _cluster_roll_bonus(self) -> int:
        """Base cluster bonus (Artemis, if any) plus HAG's range modifier."""
        band_modifier = self._band_value(short=2, medium=0, long=-2) or 0
        return super()._cluster_roll_bonus() + band_modifier
