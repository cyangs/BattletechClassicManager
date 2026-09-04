"""Cluster weapon shot resolver.

Handles missile racks (LRM, SRM) and any other weapon where ``weapon.cluster``
is True.  The cluster hits table determines how many missiles land, then the
missiles are grouped per ``weapon.cluster_damage`` and each group rolls its own
location independently.
"""

from game.cluster_hits_table import ClusterHitsTable
from game.fire.base import BaseShotResolver, roll_1d6
from game.fire.models import ClusterHit, DiceRollsResults, WeaponShot


class ClusterShotResolver(BaseShotResolver):
    """Resolves a cluster weapon hit: rolls the cluster table then scatters damage across locations."""

    def _resolve_hit(
        self,
        target_number: int,
        to_hit_roll: int,
        all_rolls: DiceRollsResults,
    ) -> WeaponShot:
        """Resolve a cluster weapon hit: roll the cluster table then scatter damage across locations."""
        """ Weapon clusters. Roll clusters and hit locations. """
        cluster_hit_roll = roll_1d6() + roll_1d6()

        if "ARTEMISIV" in self.attachments:
            cluster_hit_roll += 2

        if "ARTEMISV" in self.attachments:
            cluster_hit_roll += 3

        if cluster_hit_roll >= 12:
            cluster_hit_roll = 12

        cluster_hits = ClusterHitsTable.get_hits(
            max_cluster_size=self.weapon.num_shots,
            roll=cluster_hit_roll,
        )  # total missiles/pellets that hit

        # Damage dealt by a single missile/pellet.
        # SRM6: 12 damage / 6 shots = 2 dmg per missile
        # LRM20: 20 damage / 20 shots = 1 dmg per missile
        damage_per_missile = self.weapon.damage // self.weapon.num_shots

        # How many missiles are grouped together per location roll.
        # weapon.cluster_damage is expressed in DAMAGE, not missile count,
        # so convert it to a missile count by dividing out damage_per_missile.
        # LRM20: cluster_damage=5, damage_per_missile=1 -> 5 missiles per group
        # SRM6:  cluster_damage=2, damage_per_missile=2 -> 1 missile per group
        missiles_per_group = (self.weapon.cluster_damage or damage_per_missile) // damage_per_missile

        full_groups, remainder = divmod(cluster_hits, missiles_per_group)
        groups = [missiles_per_group] * full_groups
        if remainder:
            groups.append(remainder)

        """ Iterate through the groupings and roll location """
        group_hits: list[ClusterHit] = []
        for group_size in groups:
            """ simplify things and just roll 2D6; Dont track individual dice rolls """
            cluster_location_roll, critical_hit, _ = self._resolve_location_with_tac()
            cluster_hit_location = self._hit_location(cluster_location_roll)
            group_hits.append(
                ClusterHit(
                    location=cluster_hit_location,
                    damage=group_size * damage_per_missile,
                    critical_hit=critical_hit,
                )
            )

        """ Iterate through and the hits and sum up the total damage """
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
