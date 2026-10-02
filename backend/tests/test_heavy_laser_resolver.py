"""TDD spec for the Heavy Laser resolver.

Heavy Lasers (Clan Heavy Small/Medium/Large) hit harder and run hotter than
standard lasers, but their defining rule is a **+1 to-hit penalty** (they're
less accurate). They are NOT cluster weapons — a hit lands on a single rolled
location like any laser. So this is a thin StandardShotResolver subclass that
only adds the +1.

Run just this file::

    python -m unittest discover backend/tests -p test_heavy_laser_resolver.py -v
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game.fire.models import RangeBand
from game.fire.heavy_laser import HeavyLaserShotResolver   # noqa: E402  (RED)
from game.tables import FRONT_REAR_LOCATION_TABLE


def _heavy_laser(name="CLHeavyLargeLaser", damage=16, heat=18):
    return types.SimpleNamespace(
        name=name, full_name="Heavy Large Laser",
        damage=damage, heat=heat,
        short_range=5, medium_range=10, long_range=15,
        variable_damage=False, cluster=False,
        short_range_damage=None, medium_range_damage=None, long_range_damage=None,
        short_range_modifier=None, medium_range_modifier=None, long_range_modifier=None,
        num_shots=None, cluster_damage=None,
        modifications={"weapon_type": "HEAVY_LASER"},
    )


def _fixed(*values):
    seq = list(values)
    idx = [0]
    def _next(a, b):
        v = seq[idx[0] % len(seq)]
        idx[0] += 1
        return v
    return mock.patch("random.randint", side_effect=_next)


def _all_sixes():
    return mock.patch("random.randint", side_effect=lambda a, b: 6)


class HeavyLaserResolverTest(unittest.TestCase):

    def test_plus_one_to_hit_turns_marginal_hit_into_miss(self):
        # To-hit roll 3+4 = 7 vs target 7 would normally HIT, but the +1 raises
        # the effective target to 8, so it MISSES.
        with _fixed(3, 4):
            shot = HeavyLaserShotResolver(
                weapon=_heavy_laser(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit, "+1 should turn a 7-vs-7 into a miss")

    def test_hit_when_roll_clears_the_adjusted_target(self):
        # 4+4 = 8 >= effective target 8 (7 + 1) -> HIT.
        # Then location roll 3+4 = 7 -> Center Torso.
        with _fixed(4, 4, 3, 4):
            shot = HeavyLaserShotResolver(
                weapon=_heavy_laser(damage=16), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertEqual(shot.damage, 16)                       # single block
        self.assertIsNone(shot.cluster_hits)                     # not a cluster weapon
        self.assertEqual(shot.hit_location, FRONT_REAR_LOCATION_TABLE[7])

    def test_single_location_hit(self):
        with _all_sixes():   # to-hit 12 (hit), location 12 -> Head
            shot = HeavyLaserShotResolver(
                weapon=_heavy_laser(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertEqual(shot.hit_location, FRONT_REAR_LOCATION_TABLE[12])
        self.assertIsNone(shot.cluster_hits)

    def test_out_of_range_is_automatic_miss(self):
        shot = HeavyLaserShotResolver(
            weapon=_heavy_laser(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")


if __name__ == "__main__":
    unittest.main()
