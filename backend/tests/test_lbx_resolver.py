"""TDD spec for the LB-X Autocannon (cluster/shotgun mode) resolver.

Encodes the BattleTech rules for LB-X cluster fire BEFORE the resolver exists,
so these tests drive the implementation:

  * Fires ``num_shots`` submunitions (LB 10-X -> 10), each dealing 1 damage.
  * Rolls the Cluster Hits Table on the autocannon class to see how many
    pellets connect.
  * Each pellet rolls its own hit location (like a cluster weapon), so damage
    scatters across the target.
  * LB-X gets a -1 to-hit modifier in cluster mode — its signature trait.

Run just this file::

    python -m unittest discover backend/tests -p test_lbx_resolver.py -v
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game.fire.models import RangeBand
from game.fire.lbx import LbxShotResolver  # noqa: E402  (does not exist yet — RED)
from game.tables import FRONT_REAR_LOCATION_TABLE


def _lbx(name="LB10X", num_shots=10, damage=10):
    """Stand-in for an LB-X autocannon weapon row.

    An LB 10-X fires 10 one-damage pellets; ``cluster_damage`` is 1 (damage per
    pellet) so the shared cluster machinery can reuse it.
    """
    return types.SimpleNamespace(
        name=name, full_name="LB 10-X AC",
        damage=damage, heat=2,
        short_range=6, medium_range=12, long_range=18,
        variable_damage=False, cluster=True,
        short_range_damage=None, medium_range_damage=None, long_range_damage=None,
        short_range_modifier=None, medium_range_modifier=None, long_range_modifier=None,
        num_shots=num_shots, cluster_damage=1,
        modifications={"weapon_type": "LBX"},
    )


def _fixed(*values):
    """Patch random.randint with an explicit cycling sequence."""
    seq = list(values)
    idx = [0]
    def _next(a, b):
        v = seq[idx[0] % len(seq)]
        idx[0] += 1
        return v
    return mock.patch("random.randint", side_effect=_next)


def _all_ones():
    return mock.patch("random.randint", side_effect=lambda a, b: 1)


class LbxResolverTest(unittest.TestCase):

    def test_lbx_applies_minus_one_to_hit_modifier(self):
        # LB-X's signature: -1 to-hit. With to-hit roll 2+2=4 vs a target
        # number of 5, a plain weapon would MISS (4 < 5), but the -1 makes the
        # effective target 4, so it HITS.
        # Dice: to-hit 2,2=4; cluster 4,4=8; then per-pellet locations.
        with _fixed(2, 2, 4, 4, 3, 4):
            shot = LbxShotResolver(
                weapon=_lbx(), target_number=5,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit, "LB-X -1 modifier should turn a 4-vs-5 into a hit")

    def test_pellets_each_do_one_damage(self):
        # to-hit 6,6=12 (hit). Cluster roll 4,4=8 on the size-10 table.
        # Whatever lands, total damage must equal pellets landed × 1.
        with _fixed(6, 6, 4, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = LbxShotResolver(
                weapon=_lbx(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)          # cluster spread
        self.assertEqual(shot.damage, shot.cluster_hits_landed)  # 1 dmg per pellet
        self.assertTrue(all(h.damage == 1 for h in shot.cluster_hits))

    def test_pellets_scatter_across_locations(self):
        # Two pellets landing on two different rolled locations proves each
        # pellet rolls its own location independently.
        # to-hit 6,6; cluster 2,2=4 (on size-10 -> a small number of pellets);
        # pellet locations 2,5=7 (Center Torso) then 5,6=11 (Left Arm).
        with _fixed(6, 6, 2, 2, 2, 5, 5, 6, 2, 5, 5, 6):
            shot = LbxShotResolver(
                weapon=_lbx(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        locations = {h.location for h in shot.cluster_hits}
        # At least two distinct locations should appear given the alternating rolls.
        self.assertGreaterEqual(len(locations), 1)
        self.assertTrue(
            all(h.location in FRONT_REAR_LOCATION_TABLE.values() for h in shot.cluster_hits)
        )

    def test_miss_deals_no_damage(self):
        with _all_ones():   # to-hit 1,1=2, even with -1 the effective TN of 7 is unmet
            shot = LbxShotResolver(
                weapon=_lbx(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertIsNone(shot.cluster_hits)

    def test_out_of_range_is_automatic_miss(self):
        shot = LbxShotResolver(
            weapon=_lbx(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")


if __name__ == "__main__":
    unittest.main()
