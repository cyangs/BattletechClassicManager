"""TDD spec for the HAG (Hyper-Assault Gauss) resolver.

HAGs scatter like a cluster weapon, but their defining rule is a
**range-dependent modifier to the Cluster Hits Table roll**:

  * Short range:  +2   (more submunitions connect up close)
  * Medium range:  0
  * Long range:   -2   (fewer connect at distance)

This is distinct from a to-hit modifier — it adjusts the *cluster roll*, so
the same to-hit success yields more or fewer hits depending on range. HAG/20,
/30, /40 differ only in data (num_shots / cluster size), so one resolver
covers all three.

Run just this file::

    python -m unittest discover backend/tests -p test_hag_resolver.py -v
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game.fire.models import RangeBand
from game.fire.hag import HagShotResolver   # noqa: E402  (does not exist yet — RED)
from game.tables import FRONT_REAR_LOCATION_TABLE


def _hag(name="HAG20", num_shots=20, damage=20):
    """HAG 20: 20 one-damage submunitions, cluster scatter."""
    return types.SimpleNamespace(
        name=name, full_name="HAG/20",
        damage=damage, heat=4,
        short_range=8, medium_range=16, long_range=24,
        variable_damage=False, cluster=True,
        short_range_damage=None, medium_range_damage=None, long_range_damage=None,
        short_range_modifier=None, medium_range_modifier=None, long_range_modifier=None,
        num_shots=num_shots, cluster_damage=1,
        modifications={"weapon_type": "HAG"},
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


def _resolve_hits(range_band):
    """Resolve a HAG/20 shot at the given band with a forced base cluster roll
    of 4 (dice 2+2), returning cluster_hits_landed.

    Dice sequence consumed per shot:
      [6,6] to-hit (guaranteed hit)
      [2,2] cluster roll -> base 4, then the band modifier is applied
      [3,4,...] per-submunition location rolls (cycled, never a natural 2)
    On the size-20 table: roll 6 (short, 4+2) -> 12 hits; roll 4 (medium) -> 9;
    roll 2 (long, 4-2) -> 6. Three distinct counts prove the modifier applies.
    """
    with _fixed(6, 6, 2, 2, 3, 4):
        shot = HagShotResolver(
            weapon=_hag(), target_number=7,
            target_facing="Front/Rear", range_band=range_band,
        ).resolve()
    return shot


class HagResolverTest(unittest.TestCase):

    def test_short_range_adds_two_to_cluster_roll(self):
        shot = _resolve_hits(RangeBand.SHORT)
        self.assertTrue(shot.hit)
        # base 4 + 2 = roll 6 on size-20 -> 12 hits
        self.assertEqual(shot.cluster_hits_landed, 12)
        self.assertEqual(shot.damage, 12)   # 1 dmg per submunition

    def test_medium_range_no_modifier(self):
        shot = _resolve_hits(RangeBand.MEDIUM)
        # base 4 + 0 = roll 4 on size-20 -> 9 hits
        self.assertEqual(shot.cluster_hits_landed, 9)

    def test_long_range_subtracts_two_from_cluster_roll(self):
        shot = _resolve_hits(RangeBand.LONG)
        # base 4 - 2 = roll 2 on size-20 -> 6 hits
        self.assertEqual(shot.cluster_hits_landed, 6)

    def test_hit_scatters_across_locations(self):
        shot = _resolve_hits(RangeBand.MEDIUM)
        self.assertIsNone(shot.hit_location)   # cluster spread, no single location
        self.assertIsNotNone(shot.cluster_hits)
        self.assertTrue(all(h.location in FRONT_REAR_LOCATION_TABLE.values()
                            for h in shot.cluster_hits))

    def test_miss_deals_no_damage(self):
        with _all_ones():   # to-hit 1,1=2 < 7
            shot = HagShotResolver(
                weapon=_hag(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertIsNone(shot.cluster_hits)

    def test_out_of_range_is_automatic_miss(self):
        shot = HagShotResolver(
            weapon=_hag(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")

    def test_targeting_computer_does_not_change_hag_cluster_roll(self):
        # A TC aids a HAG with a -1 TO-HIT, applied in combat routing by lowering
        # the target number BEFORE the resolver runs. The resolver itself must
        # NOT alter the cluster roll for TC. Verify scatter is unaffected: at
        # MEDIUM the band modifier is 0, so base cluster roll 4 (2+2) -> 9 hits
        # regardless of the targeting_computer_active flag.
        with _fixed(6, 6, 2, 2, 3, 4):
            shot = HagShotResolver(
                weapon=_hag(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.MEDIUM,
                targeting_computer_active=True,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertEqual(shot.cluster_hits_landed, 9)


if __name__ == "__main__":
    unittest.main()
