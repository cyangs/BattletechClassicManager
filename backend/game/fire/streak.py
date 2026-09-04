"""Streak weapon resolver

If it is a streak, everything hits.
"""

from game.cluster_hits_table import ClusterHitsTable
from game.fire.base import BaseShotResolver, roll_1d6
from game.fire.models import ClusterHit, DiceRollsResults, WeaponShot


class StreakShotResolver(BaseShotResolver):
    """Resolves a Streak weapon"""

    def _resolve_hit(
        self,
        target_number: int,
        to_hit_roll: int,
        all_rolls: DiceRollsResults,
    ) -> WeaponShot:
        """Resolve a streak weapon hit. All rounds hit."""
        cluster_hit_roll = 12 ## cheap way of resolving everything hits.
        cluster_hits = ClusterHitsTable.get_hits(
            max_cluster_size=self.weapon.num_shots,
            roll=cluster_hit_roll,
        )

        """ Iterate through the groupings and roll location """
        group_hits: list[ClusterHit] = []
        for _ in range(cluster_hits):
            """ simplify things and just roll 2D6; Dont track individual dice rolls """
            cluster_location_roll, critical_hit, _ = self._resolve_location_with_tac()
            cluster_hit_location = self._hit_location(cluster_location_roll)
            group_hits.append(
                ClusterHit(
                    location=cluster_hit_location,
                    damage=self.weapon.cluster_damage,
                    critical_hit=critical_hit,
                )
            )

        """ Iterate through and the hits and sum up the total damage """
        # Damage dealt by a single burst.
        # ULTRA AC 10: 10 damage * NUM cluster hits = 20 damage total.
        total_damage = sum(hit.damage for hit in group_hits)

        """ A cluster spread has no single hit location; damage is the total that landed. """
        return self._shot(
            target_number=target_number,
            roll=to_hit_roll,
            hit=True,
            hit_location=None,
            damage=total_damage,
            all_rolls=all_rolls,
            cluster_roll=cluster_hit_roll,
            cluster_hits_landed=cluster_hits,
            cluster_hits=group_hits,
        )
