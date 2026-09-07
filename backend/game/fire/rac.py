"""Rotary Autocannon (RAC) shot resolver.

A Rotary AC fires a declared number of rounds (``weapon.num_shots``, 1-6) in a
single action:

  * A natural to-hit roll of 2 JAMS the weapon — no damage, and the shot is
    flagged ``jammed`` so the UI can show it needs clearing.
  * Otherwise, on a hit the Cluster Hits Table (rolled on the declared shot
    count) decides how many rounds connect. Each connecting round deals the
    AC's per-shot damage (``weapon.cluster_damage``) to its own independently
    rolled hit location.

The jam check inspects the raw to-hit dice, so this overrides ``resolve``
rather than just ``_resolve_hit``.
"""

from game.cluster_hits_table import ClusterHitsTable
from game.fire.base import BaseShotResolver, roll_1d6
from game.fire.models import ClusterHit, DiceRollsResults, WeaponShot


class RacShotResolver(BaseShotResolver):
    """Rotary AC: variable rounds via the cluster table, with a jam on a natural 2."""

    def resolve(self) -> WeaponShot:
        """Roll the to-hit, checking for a jam before resolving damage."""
        # Out of range -> automatic miss (matches the base behaviour).
        if self.target_number is None:
            return self._shot(hit_location="Target Out of Range")

        to_hit_1, to_hit_2 = roll_1d6(), roll_1d6()
        to_hit_roll = to_hit_1 + to_hit_2
        all_rolls = DiceRollsResults(to_hit_1, to_hit_2)

        # A natural 2 jams the rotary mechanism: no damage this action.
        if to_hit_roll == 2:
            return self._shot(
                target_number=self._adjusted_target_number(),
                roll=to_hit_roll,
                hit=False,
                hit_location="Jammed",
                all_rolls=all_rolls,
                jammed=True,
            )

        target_number = self._adjusted_target_number()
        if to_hit_roll < target_number:
            return self._shot(
                target_number=target_number,
                roll=to_hit_roll,
                hit=False,
                hit_location="Miss",
                all_rolls=all_rolls,
            )

        return self._resolve_hit(target_number, to_hit_roll, all_rolls)

    def _resolve_hit(
        self,
        target_number: int,
        to_hit_roll: int,
        all_rolls: DiceRollsResults,
    ) -> WeaponShot:
        """Roll the cluster table on the declared shot count; each round hits its own location."""
        cluster_hit_roll = roll_1d6() + roll_1d6()
        rounds_hit = ClusterHitsTable.get_hits(
            max_cluster_size=self.weapon.num_shots,
            roll=cluster_hit_roll,
        )

        # Each connecting round deals the AC's per-shot damage to its own location.
        damage_per_round = self.weapon.cluster_damage

        group_hits: list[ClusterHit] = []
        for _ in range(rounds_hit):
            location_roll, critical_hit, _ = self._resolve_location_with_tac()
            group_hits.append(
                ClusterHit(
                    location=self._hit_location(location_roll),
                    damage=damage_per_round,
                    critical_hit=critical_hit,
                )
            )

        total_damage = sum(hit.damage for hit in group_hits)

        return self._shot(
            target_number=target_number,
            roll=to_hit_roll,
            hit=True,
            hit_location=None,
            damage=total_damage,
            all_rolls=all_rolls,
            cluster_roll=cluster_hit_roll,
            cluster_hits_landed=rounds_hit,
            cluster_hits=group_hits,
        )
