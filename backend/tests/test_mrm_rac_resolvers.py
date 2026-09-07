"""TDD spec for the MRM and Rotary AC resolvers.

MRM (Medium-Range Missiles)
  * Cluster weapon (scatters like LRM/SRM).
  * Flat +1 to-hit penalty — its defining trait — and no Artemis benefit.

Rotary AC (RAC)
  * Fires a declared number of rounds (weapon.num_shots, 1-6) in one action.
  * The Cluster Hits Table (on the declared shot count) decides how many rounds
    connect; each connecting round deals the AC's per-shot damage to its own
    independently-rolled location.
  * Jam risk: a natural to-hit roll of 2 jams the weapon — no damage, and the
    shot is flagged jammed.

Run just this file::

    python -m unittest discover backend/tests -p test_mrm_rac_resolvers.py -v
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game.fire.models import RangeBand
from game.fire.mrm import MrmShotResolver   # noqa: E402  (does not exist yet — RED)
from game.fire.rac import RacShotResolver   # noqa: E402  (does not exist yet — RED)
from game.tables import FRONT_REAR_LOCATION_TABLE


def _mrm(name="MRM20", num_shots=20, damage=20, cluster_damage=1):
    """MRM 20: 20 one-damage missiles, +1 to-hit, cluster spread."""
    return types.SimpleNamespace(
        name=name, full_name="MRM 20",
        damage=damage, heat=6,
        short_range=3, medium_range=8, long_range=15,
        variable_damage=False, cluster=True,
        short_range_damage=None, medium_range_damage=None, long_range_damage=None,
        short_range_modifier=None, medium_range_modifier=None, long_range_modifier=None,
        num_shots=num_shots, cluster_damage=cluster_damage,
        modifications={"weapon_type": "MRM"},
    )


def _rac(name="RAC5", num_shots=2, damage=5):
    """Rotary AC/5 firing `num_shots` rounds of 5 damage each."""
    return types.SimpleNamespace(
        name=name, full_name="Rotary AC/5",
        damage=damage, heat=1,
        short_range=5, medium_range=10, long_range=15,
        variable_damage=False, cluster=True,
        short_range_damage=None, medium_range_damage=None, long_range_damage=None,
        short_range_modifier=None, medium_range_modifier=None, long_range_modifier=None,
        num_shots=num_shots, cluster_damage=damage,  # per-round damage
        modifications={"weapon_type": "RAC"},
    )


def _fixed(*values):
    seq = list(values)
    idx = [0]
    def _next(a, b):
        v = seq[idx[0] % len(seq)]
        idx[0] += 1
        return v
    return mock.patch("random.randint", side_effect=_next)


def _all_ones():
    return mock.patch("random.randint", side_effect=lambda a, b: 1)


# ---------------------------------------------------------------------------
# MRM
# ---------------------------------------------------------------------------

class MrmResolverTest(unittest.TestCase):

    def test_mrm_applies_plus_one_to_hit_penalty(self):
        # +1 penalty: to-hit roll 3+4=7 vs target 7 would normally HIT, but the
        # +1 makes the effective target 8, so it MISSES.
        with _fixed(3, 4):
            shot = MrmShotResolver(
                weapon=_mrm(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit, "MRM +1 penalty should turn a 7-vs-7 into a miss")

    def test_mrm_hit_scatters_like_cluster(self):
        # to-hit 6,6=12 (comfortably beats 7 even with +1). Then cluster scatter.
        with _fixed(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = MrmShotResolver(
                weapon=_mrm(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)         # cluster spread
        self.assertIsNotNone(shot.cluster_hits)
        self.assertEqual(shot.damage, shot.cluster_hits_landed)  # 1 dmg per missile

    def test_mrm_out_of_range_auto_miss(self):
        shot = MrmShotResolver(
            weapon=_mrm(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")


# ---------------------------------------------------------------------------
# Rotary AC
# ---------------------------------------------------------------------------

class RacResolverTest(unittest.TestCase):

    def test_rac_jams_on_natural_two(self):
        # A natural to-hit roll of 2 (1+1) jams the weapon: no damage, flagged.
        with _all_ones():
            shot = RacShotResolver(
                weapon=_rac(num_shots=6), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertTrue(getattr(shot, "jammed", False), "natural 2 should jam the RAC")

    def test_rac_hit_scatters_rounds_at_per_shot_damage(self):
        # to-hit 6,6=12 (hit, not a jam). Declared 2 rounds -> cluster table on
        # size 2. Cluster roll 6,6=12 -> both rounds hit. Each round is 5 damage
        # to its own location.
        with _fixed(6, 6, 6, 6, 3, 4, 3, 4):
            shot = RacShotResolver(
                weapon=_rac(num_shots=2, damage=5), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertFalse(getattr(shot, "jammed", False))
        self.assertIsNone(shot.hit_location)               # scatter
        self.assertEqual(shot.cluster_hits_landed, 2)      # both rounds landed
        self.assertEqual(shot.damage, 10)                  # 2 × 5
        self.assertTrue(all(h.damage == 5 for h in shot.cluster_hits))

    def test_rac_partial_rounds_hit(self):
        # to-hit 6,6=12 (hit). Declared 6 rounds. Cluster roll 2,2=4 on size-6
        # -> a partial number of rounds land; total damage = rounds × 5.
        with _fixed(6, 6, 2, 2, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = RacShotResolver(
                weapon=_rac(num_shots=6, damage=5), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertEqual(shot.damage, shot.cluster_hits_landed * 5)
        self.assertTrue(all(h.location in FRONT_REAR_LOCATION_TABLE.values()
                            for h in shot.cluster_hits))

    def test_rac_plain_miss_is_not_a_jam(self):
        # to-hit 2,3=5 vs target 7 -> a normal miss (not a natural 2), no jam.
        with _fixed(2, 3):
            shot = RacShotResolver(
                weapon=_rac(num_shots=6), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertFalse(getattr(shot, "jammed", False))
        self.assertEqual(shot.damage, 0)

    def test_rac_out_of_range_auto_miss(self):
        shot = RacShotResolver(
            weapon=_rac(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")


if __name__ == "__main__":
    unittest.main()
