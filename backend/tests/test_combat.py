"""Unit tests for the fire resolution system.

``backend`` must be on ``sys.path``. The insert below handles that regardless
of where the tests are run from::

    python -m unittest discover backend/tests -v
    # or, from the repo root:
    python -m pytest backend/tests/test_combat.py

Dice are deterministic: ``roll_1d6`` lives in :mod:`game.fire.base` and is
monkeypatched there so every resolver that imports it picks up the patch.
The database is replaced with an in-memory ``FakeWeaponRepository``.
"""

import json
import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

# game.fire.base is the single source of roll_1d6, but each submodule binds
# it at import time. Patching random.randint reaches all of them uniformly.
from game.fire import (
    RangeBand,
    RANGE_BAND_MODIFIER,
    DiceRollsResults,
    ClusterHit,
    WeaponShot,
    BaseShotResolver,
    StandardShotResolver,
    ClusterShotResolver,
    UltraShotResolver,
    serialize_shot,
    roll_1d6,
    roll_2d6,
)
from game.fire.streak import StreakShotResolver
from game.combat import CombatResolver
from game.tables import (
    FRONT_REAR_LOCATION_TABLE,
    LEFT_SIDE_LOCATION_TABLE,
    RIGHT_SIDE_LOCATION_TABLE,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _weapon(
        name="MediumLaser",
        full_name="Medium Laser",
        damage=5,
        heat=3,
        short_range=3,
        medium_range=6,
        long_range=9,
        variable_damage=False,
        cluster=False,
        short_range_damage=None,
        medium_range_damage=None,
        long_range_damage=None,
        short_range_modifier=None,
        medium_range_modifier=None,
        long_range_modifier=None,
        num_shots=None,
        cluster_damage=None,
        modifications=None,
):
    """Build a stand-in for a ``Weapon`` ORM row (attribute access only)."""
    return types.SimpleNamespace(
        name=name,
        full_name=full_name,
        damage=damage,
        heat=heat,
        short_range=short_range,
        medium_range=medium_range,
        long_range=long_range,
        variable_damage=variable_damage,
        cluster=cluster,
        short_range_damage=short_range_damage,
        medium_range_damage=medium_range_damage,
        long_range_damage=long_range_damage,
        short_range_modifier=short_range_modifier,
        medium_range_modifier=medium_range_modifier,
        long_range_modifier=long_range_modifier,
        num_shots=num_shots,
        cluster_damage=cluster_damage,
        modifications=modifications,
    )


def _attachment(sku):
    """Minimal stand-in for a mech attachment."""
    return types.SimpleNamespace(attachment_sku=sku)


def _unit(name="Atlas", attachments=None):
    """Stand-in for a ``SessionMech`` firing unit.

    ``resolve_fire`` reads ``unit.master_mech.name`` for the attacker label
    and iterates ``unit.attachments`` for the targeting-computer check.
    """
    return types.SimpleNamespace(
        master_mech=types.SimpleNamespace(name=name),
        attachments=attachments if attachments is not None else [],
    )


class FakeWeaponRepository:
    """In-memory stand-in for WeaponRepository keyed on ``Weapon.name``."""

    def __init__(self, *weapons):
        self._by_name = {w.name: w for w in weapons}

    def fetch_weapon_by_name(self, name):
        return self._by_name.get(name)


def _resolver(*weapons):
    return CombatResolver(FakeWeaponRepository(*weapons))


class FixedDice:
    """Callable that yields a fixed, cycling sequence of die values (kept for reference)."""

    def __init__(self, *values):
        self.values = list(values)
        self.calls = 0

    def __call__(self):
        v = self.values[self.calls % len(self.values)]
        self.calls += 1
        return v


def _all_sixes():
    """Patch random.randint so every die returns 6 (to-hit 12, location 12 -> Head)."""
    return mock.patch("random.randint", side_effect=lambda a, b: 6)


def _all_ones():
    """Patch random.randint so every die returns 1 (to-hit 2 -> guaranteed miss)."""
    return mock.patch("random.randint", side_effect=lambda a, b: 1)


def _fixed(*values):
    """Patch random.randint with an explicit cycling sequence of values."""
    seq = list(values)
    idx = [0]
    def _next(a, b):
        v = seq[idx[0] % len(seq)]
        idx[0] += 1
        return v
    return mock.patch("random.randint", side_effect=_next)


# ---------------------------------------------------------------------------
# Dice helper tests
# ---------------------------------------------------------------------------

class DiceRollHelpersTest(unittest.TestCase):
    def test_roll_1d6_in_range(self):
        for _ in range(200):
            self.assertIn(roll_1d6(), range(1, 7))

    def test_roll_2d6_in_range(self):
        for _ in range(200):
            self.assertIn(roll_2d6(), range(2, 13))


class DiceRollsResultsTest(unittest.TestCase):
    def test_location_dice_default_to_none(self):
        dice = DiceRollsResults(to_hit_1=3, to_hit_2=4)
        self.assertIsNone(dice.location_1)
        self.assertIsNone(dice.location_2)


# ---------------------------------------------------------------------------
# StandardShotResolver
# ---------------------------------------------------------------------------

class StandardShotResolverTest(unittest.TestCase):
    def _shot(self, target_number, facing="Front/Rear", range_band=RangeBand.SHORT, damage=5):
        return StandardShotResolver(
            weapon=_weapon(name="AC20", full_name="AC/20", damage=damage),
            target_number=target_number,
            target_facing=facing,
            range_band=range_band,
        ).resolve()

    def test_out_of_range_is_an_automatic_miss(self):
        shot = self._shot(target_number=None)
        self.assertFalse(shot.hit)
        self.assertEqual(shot.roll, 0)
        self.assertEqual(shot.damage, 0)
        self.assertEqual(shot.hit_location, "Target Out of Range")
        self.assertIsNone(shot.all_rolls)

    def test_hit_keeps_damage_and_sets_location(self):
        with _all_sixes():  # to-hit 12 >= 7, location 12 -> Head
            shot = self._shot(target_number=7, damage=20)
        self.assertTrue(shot.hit)
        self.assertEqual(shot.roll, 12)
        self.assertEqual(shot.damage, 20)
        self.assertEqual(shot.hit_location, FRONT_REAR_LOCATION_TABLE[12])

    def test_miss_zeroes_damage(self):
        with _all_ones():  # to-hit 2 < 7
            shot = self._shot(target_number=7, damage=20)
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertEqual(shot.hit_location, "Miss")

    def test_left_side_facing_uses_left_table(self):
        with _fixed(6, 6, 1, 4):
            # to-hit 6+6=12 (hit), location 1+4=5
            shot = self._shot(target_number=7, facing="Left Side")
        self.assertEqual(shot.hit_location, LEFT_SIDE_LOCATION_TABLE[5])

    def test_right_side_facing_uses_right_table(self):
        with _fixed(6, 6, 3, 3):
            # to-hit 12 (hit), location 3+3=6
            shot = self._shot(target_number=7, facing="Right Side")
        self.assertEqual(shot.hit_location, RIGHT_SIDE_LOCATION_TABLE[6])

    def test_weapon_range_modifier_applied_per_band(self):
        """Pulse laser: signed per-band modifier is added to the target number."""
        weapon = _weapon(name="Pulse", short_range_modifier=-3,
                         medium_range_modifier=-2, long_range_modifier=-1)
        expected = {
            RangeBand.SHORT: 10 - 3,
            RangeBand.MEDIUM: 10 - 2,
            RangeBand.LONG: 10 - 1,
        }
        for band, tn in expected.items():
            shot = StandardShotResolver(
                weapon=weapon, target_number=10,
                target_facing="Front/Rear", range_band=band,
            ).resolve()
            self.assertEqual(shot.target_number, tn, band)

    def test_no_range_modifier_leaves_target_number_unchanged(self):
        weapon = _weapon(name="ML")
        shot = StandardShotResolver(
            weapon=weapon, target_number=7,
            target_facing="Front/Rear", range_band=RangeBand.SHORT,
        ).resolve()
        self.assertEqual(shot.target_number, 7)

    def test_variable_damage_uses_band_specific_value(self):
        weapon = _weapon(
            name="Pulse", damage=0, variable_damage=True,
            short_range_damage=10, medium_range_damage=7, long_range_damage=4,
        )
        with _all_sixes():
            shot = StandardShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertEqual(shot.damage, 4)

    def test_variable_damage_falls_back_to_flat_when_band_null(self):
        weapon = _weapon(name="Pulse", damage=6, variable_damage=True,
                         short_range_damage=None)
        with _all_sixes():
            shot = StandardShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertEqual(shot.damage, 6)

    def test_serialize_shot_is_json_safe(self):
        with _all_sixes():
            shot = StandardShotResolver(
                weapon=_weapon(name="ML", full_name="Medium Laser", damage=5),
                target_number=7,
                target_facing="Front/Rear",
                range_band=RangeBand.MEDIUM,
            ).resolve()
        d = serialize_shot(shot)
        self.assertEqual(d["weapon"], "Medium Laser")
        self.assertEqual(d["range_band"], "MEDIUM")
        json.dumps(d)  # must not raise

    # -- critical hits ---------------------------------------------------

    def test_critical_hit_rerolls_location_and_flags(self):
        # to-hit 6+6=12 (hit), location 1+1=2 (TAC), reroll 3+4=7 -> Center Torso
        weapon = _weapon(name="ML", damage=5)
        with _fixed(6, 6, 1, 1, 3, 4):
            shot = StandardShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertTrue(shot.critical_hit)
        self.assertEqual((shot.all_rolls.location_1, shot.all_rolls.location_2), (1, 1))
        self.assertEqual((shot.all_rolls.tac_reroll_1, shot.all_rolls.tac_reroll_2), (3, 4))
        self.assertEqual(shot.hit_location, FRONT_REAR_LOCATION_TABLE[7])
        self.assertTrue(serialize_shot(shot)["critical_hit"])

    def test_non_critical_hit_has_no_reroll_dice(self):
        weapon = _weapon(name="ML", damage=5)
        with _fixed(6, 6, 3, 4):
            shot = StandardShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.critical_hit)
        self.assertIsNone(shot.all_rolls.tac_reroll_1)
        self.assertIsNone(shot.all_rolls.tac_reroll_2)

    def test_all_rolls_populated_on_hit(self):
        with _fixed(4, 3, 2, 5):
            # to-hit 4+3=7 (hit vs TN 7), location 2+5=7
            shot = StandardShotResolver(
                weapon=_weapon(name="ML"), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertEqual(shot.all_rolls.to_hit_1, 4)
        self.assertEqual(shot.all_rolls.to_hit_2, 3)
        self.assertEqual(shot.all_rolls.location_1, 2)
        self.assertEqual(shot.all_rolls.location_2, 5)


# ---------------------------------------------------------------------------
# ClusterShotResolver
# ---------------------------------------------------------------------------

class ClusterShotResolverTest(unittest.TestCase):
    def test_lrm20_splits_damage_across_locations(self):
        # LRM 20: to-hit 6+6=12, cluster 4+5=9 -> 16 hits on size-20 table.
        # damage_per_missile=1, missiles_per_group=5 -> groups [5,5,5,1].
        # Each group location 3+4=7 -> Center Torso.
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20,
                         cluster_damage=5, damage=20)
        with _fixed(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = ClusterShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)
        self.assertEqual(shot.cluster_roll, 9)
        self.assertEqual(shot.cluster_hits_landed, 16)
        self.assertEqual(shot.damage, 16)
        self.assertEqual([h.damage for h in shot.cluster_hits], [5, 5, 5, 1])
        self.assertTrue(all(h.location == FRONT_REAR_LOCATION_TABLE[7]
                            for h in shot.cluster_hits))

    def test_srm6_splits_damage_correctly(self):
        # SRM 6: damage=12, num_shots=6, cluster_damage=2.
        # damage_per_missile=2, missiles_per_group=1 -> 5 groups of 1.
        # to-hit 6+6=12, cluster 4+5=9 -> 5 hits on size-6 table.
        weapon = _weapon(name="SRM6", full_name="SRM 6", cluster=True,
                         num_shots=6, cluster_damage=2, damage=12)
        with _fixed(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = ClusterShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)
        self.assertEqual(shot.cluster_hits_landed, 5)
        self.assertEqual(shot.damage, 10)
        self.assertEqual([h.damage for h in shot.cluster_hits], [2, 2, 2, 2, 2])

    def test_cluster_miss_deals_no_damage(self):
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20,
                         cluster_damage=5, damage=20)
        with _all_ones():
            shot = ClusterShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertIsNone(shot.cluster_hits)

    def test_cluster_critical_hit_flags_individual_groups(self):
        # LRM20: to-hit 6+6=12, cluster 1+1=2 -> 6 hits, groups [5, 1].
        # First group location 1+1=2 (TAC) -> reroll 3+4=7. Second 3+4=7 (no crit).
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20,
                         cluster_damage=5, damage=20)
        with _fixed(6, 6, 1, 1, 1, 1, 3, 4, 3, 4):
            shot = ClusterShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertEqual([h.critical_hit for h in shot.cluster_hits], [True, False])
        self.assertEqual(shot.cluster_hits[0].location, FRONT_REAR_LOCATION_TABLE[7])

    def test_cluster_shot_serializes_to_json(self):
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20,
                         cluster_damage=5, damage=20)
        with _fixed(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = ClusterShotResolver(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        d = serialize_shot(shot)
        self.assertEqual(d["cluster_hits_landed"], 16)
        self.assertEqual([h["damage"] for h in d["cluster_hits"]], [5, 5, 5, 1])
        json.dumps(d)  # must not raise


# ---------------------------------------------------------------------------
# UltraShotResolver
# ---------------------------------------------------------------------------

class UltraShotResolverTest(unittest.TestCase):
    """ULTRA double-tap: cluster table determines how many rounds hit, each
    to its own independently-rolled location for weapon.cluster_damage damage."""

    def _ultra(self, cluster_damage=10, num_shots=2):
        return _weapon(
            name="UAC10", full_name="Ultra AC/10",
            damage=10, num_shots=num_shots, cluster_damage=cluster_damage,
            modifications={"weapon_type": "ULTRA"},
        )

    def test_both_rounds_hit_doubles_damage(self):
        # to-hit 6+6=12 (hit), cluster 6+6=12 -> 2 hits on size-2 table.
        # Each round location 3+4=7 -> Center Torso, damage=10.
        with _fixed(6, 6, 6, 6, 3, 4, 3, 4):
            shot = UltraShotResolver(
                weapon=self._ultra(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)
        self.assertEqual(shot.cluster_hits_landed, 2)
        self.assertEqual(shot.damage, 20)
        self.assertEqual(len(shot.cluster_hits), 2)
        self.assertEqual(shot.cluster_hits[0].damage, 10)
        self.assertEqual(shot.cluster_hits[1].damage, 10)

    def test_one_round_hits(self):
        # to-hit 6+6=12, cluster 1+1=2 -> 1 hit on size-2 table.
        with _fixed(6, 6, 1, 1, 3, 4):
            shot = UltraShotResolver(
                weapon=self._ultra(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertEqual(shot.cluster_hits_landed, 1)
        self.assertEqual(shot.damage, 10)
        self.assertEqual(len(shot.cluster_hits), 1)

    def test_to_hit_miss_deals_no_damage(self):
        with _all_ones():
            shot = UltraShotResolver(
                weapon=self._ultra(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertIsNone(shot.cluster_hits)

    def test_out_of_range_is_automatic_miss(self):
        shot = UltraShotResolver(
            weapon=self._ultra(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")

    def test_each_round_rolls_location_independently(self):
        # to-hit 6+6=12, cluster 6+6=12 -> 2 hits.
        # Round 1: location 2+5=7 -> Center Torso (no TAC, sum != 2)
        # Round 2: location 5+6=11 -> Left Arm (Front/Rear table)
        with _fixed(6, 6, 6, 6, 2, 5, 5, 6):
            shot = UltraShotResolver(
                weapon=self._ultra(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        locations = [h.location for h in shot.cluster_hits]
        self.assertEqual(locations[0], FRONT_REAR_LOCATION_TABLE[7])
        self.assertEqual(locations[1], FRONT_REAR_LOCATION_TABLE[11])

    def test_critical_hit_on_ultra_round(self):
        # to-hit 6+6=12, cluster 1+1=2 -> 1 hit. Location 1+1=2 (TAC) -> reroll 3+4=7.
        with _fixed(6, 6, 1, 1, 1, 1, 3, 4):
            shot = UltraShotResolver(
                weapon=self._ultra(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.cluster_hits[0].critical_hit)
        self.assertEqual(shot.cluster_hits[0].location, FRONT_REAR_LOCATION_TABLE[7])

    def test_ultra_shot_serializes_to_json(self):
        with _fixed(6, 6, 6, 6, 3, 4, 3, 4):
            shot = UltraShotResolver(
                weapon=self._ultra(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        d = serialize_shot(shot)
        self.assertEqual(d["cluster_hits_landed"], 2)
        self.assertEqual(d["damage"], 20)
        json.dumps(d)  # must not raise


# ---------------------------------------------------------------------------
# StreakShotResolver
# ---------------------------------------------------------------------------

class StreakShotResolverTest(unittest.TestCase):
    """Streak SRMs: all missiles always hit, each gets an independent location."""

    def _streak(self, num_shots=6, cluster_damage=2):
        return _weapon(
            name="SSRM6", full_name="Streak SRM 6",
            damage=12, num_shots=num_shots, cluster_damage=cluster_damage,
            modifications={"weapon_type": "STREAK"},
        )

    def test_all_missiles_hit_on_a_to_hit_success(self):
        # to-hit 6+6=12 (hit). Size-6 cluster at roll=12 -> 6 hits.
        # Each location 3+4=7 -> Center Torso.
        with _fixed(6, 6, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = StreakShotResolver(
                weapon=self._streak(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertEqual(shot.cluster_hits_landed, 6)   # max hits (roll=12 on size-6)
        self.assertEqual(shot.damage, 12)                # 6 × 2
        self.assertEqual(len(shot.cluster_hits), 6)
        self.assertEqual(shot.cluster_roll, 12)          # Streak always uses 12

    def test_each_missile_rolls_location_independently(self):
        # to-hit 6+6=12. Size-6 at roll=12 -> 6 hits.
        # Two different location rolls to confirm independence.
        with _fixed(6, 6, 2, 5, 5, 6, 2, 5, 5, 6, 2, 5, 5, 6):
            shot = StreakShotResolver(
                weapon=self._streak(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        locations = [h.location for h in shot.cluster_hits]
        # 2+5=7 -> Center Torso, 5+6=11 -> Left Arm (alternating)
        self.assertIn(FRONT_REAR_LOCATION_TABLE[7], locations)
        self.assertIn(FRONT_REAR_LOCATION_TABLE[11], locations)

    def test_streak_miss_deals_no_damage(self):
        with _all_ones():
            shot = StreakShotResolver(
                weapon=self._streak(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertIsNone(shot.cluster_hits)

    def test_streak_out_of_range(self):
        shot = StreakShotResolver(
            weapon=self._streak(), target_number=None,
            target_facing="Front/Rear", range_band=None,
        ).resolve()
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Target Out of Range")

    def test_streak_serializes_to_json(self):
        with _fixed(6, 6, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4):
            shot = StreakShotResolver(
                weapon=self._streak(), target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        d = serialize_shot(shot)
        self.assertEqual(d["cluster_hits_landed"], 6)
        json.dumps(d)  # must not raise


# ---------------------------------------------------------------------------
# CombatResolver — resolve_fire integration
# ---------------------------------------------------------------------------

class ResolveFireTest(unittest.TestCase):
    # -- database lookup -------------------------------------------------

    def test_looks_weapon_up_by_name_and_uses_db_stats(self):
        resolver = _resolver(_weapon(name="AC20", full_name="AC/20", damage=20, heat=7))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["AC20"], pilot_gunnery_skill=4)
        shot = result["shots"][0]
        self.assertEqual(shot["weapon"], "AC/20")
        self.assertEqual(shot["damage"], 20)
        self.assertEqual(result["total_heat"], 7)

    def test_unknown_weapon_name_is_reported_not_dropped(self):
        resolver = _resolver(_weapon(name="AC20"))
        result = resolver.resolve_fire(_unit(), ["AC20", "Nope"], pilot_gunnery_skill=4)
        self.assertEqual(result["unresolved_weapons"], ["Nope"])
        self.assertEqual(len(result["shots"]), 1)

    def test_repeated_lookup_is_cached_single_db_hit(self):
        repo = FakeWeaponRepository(_weapon(name="ML"))
        repo.fetch_weapon_by_name = mock.Mock(side_effect=repo.fetch_weapon_by_name)
        CombatResolver(repo).resolve_fire(_unit(), ["ML", "ML", "ML"], pilot_gunnery_skill=4)
        self.assertEqual(repo.fetch_weapon_by_name.call_count, 1)

    # -- guaranteed hit / miss ------------------------------------------

    def test_guaranteed_hit_applies_full_damage(self):
        resolver = _resolver(_weapon(name="ML", damage=20))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4)
        self.assertEqual(result["hits"], 1)
        self.assertEqual(result["total_damage"], 20)

    def test_guaranteed_miss_deals_no_damage_but_accrues_heat(self):
        resolver = _resolver(_weapon(name="ML", damage=20, heat=7))
        with _all_ones():
            result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4)
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["total_damage"], 0)
        self.assertEqual(result["total_heat"], 7)
        self.assertEqual(result["shots"][0]["hit_location"], "Miss")

    # -- shot count (name repeated per shot) ----------------------------

    def test_repeated_name_fires_once_per_entry(self):
        resolver = _resolver(_weapon(name="ML", damage=1))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["ML"] * 4, pilot_gunnery_skill=4)
        self.assertEqual(len(result["shots"]), 4)
        self.assertEqual(result["total_damage"], 4)

    # -- target number composition --------------------------------------

    def test_target_number_is_gunnery_plus_range_bracket(self):
        resolver = _resolver(_weapon(name="ML"))
        # distance 5 is medium bracket (+2)
        result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4,
                                       distance_modifier=5)
        self.assertEqual(result["shots"][0]["target_number"], 4 + 2)
        self.assertEqual(result["shots"][0]["range_band"], "MEDIUM")

    def test_gator_modifiers_stack(self):
        resolver = _resolver(_weapon(name="ML"))
        # G=3, A=1, T=2, O=1, R=0 (short bracket at distance 2)
        result = resolver.resolve_fire(
            _unit(), ["ML"], pilot_gunnery_skill=3, distance_modifier=2,
            target_movement_modifier=2, self_movement_modifier=1, additional_modifier=1,
        )
        self.assertEqual(result["shots"][0]["target_number"], 3 + 1 + 2 + 1)

    def test_target_number_does_not_compound_across_shots(self):
        resolver = _resolver(_weapon(name="ML"))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["ML", "ML"], pilot_gunnery_skill=4,
                                           distance_modifier=8)  # long bracket
        tns = {s["target_number"] for s in result["shots"]}
        self.assertEqual(tns, {4 + 4})

    # -- out of range ---------------------------------------------------

    def test_beyond_long_range_is_out_of_range(self):
        resolver = _resolver(_weapon(name="ML", long_range=9))
        result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4,
                                       distance_modifier=15)
        shot = result["shots"][0]
        self.assertIsNone(shot["target_number"])
        self.assertFalse(shot["hit"])
        self.assertEqual(shot["damage"], 0)
        self.assertEqual(shot["hit_location"], "Target Out of Range")
        self.assertIsNone(shot["range_band"])

    # -- return shape ---------------------------------------------------

    def test_result_contains_expected_keys(self):
        resolver = _resolver(_weapon(name="ML"))
        result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4,
                                       target_name="Locust")
        for key in ("attacker", "target", "target_movement_modifier", "shots",
                    "hits", "misses", "total_damage", "total_heat", "unresolved_weapons"):
            self.assertIn(key, result)
        self.assertEqual(result["attacker"], "Atlas")
        self.assertEqual(result["target"], "Locust")

    def test_result_is_json_serializable(self):
        resolver = _resolver(_weapon(name="ML", full_name="Medium Laser"))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4,
                                           distance_modifier=2)
        json.dumps(result)
        self.assertIsInstance(result["shots"][0]["weapon"], str)

    def test_hits_plus_misses_equals_shot_count(self):
        resolver = _resolver(_weapon(name="ML"))
        result = resolver.resolve_fire(_unit(), ["ML"] * 5, pilot_gunnery_skill=4)
        self.assertEqual(result["hits"] + result["misses"], len(result["shots"]))

    def test_no_weapons_yields_empty_result(self):
        result = _resolver().resolve_fire(_unit(), [], pilot_gunnery_skill=4)
        self.assertEqual(result["shots"], [])
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["total_damage"], 0)


# ---------------------------------------------------------------------------
# Resolver routing — combat.py picks the right subclass
# ---------------------------------------------------------------------------

class ResolverRoutingTest(unittest.TestCase):
    """CombatResolver must instantiate the correct resolver class per weapon."""

    def _fire(self, weapon, *, distance=1, double_tap_flags=None, unit=None):
        return _resolver(weapon).resolve_fire(
            unit or _unit(), [weapon.name],
            pilot_gunnery_skill=4,
            distance_modifier=distance,
            double_tap_flags=double_tap_flags,
        )

    def test_standard_weapon_uses_standard_resolver(self):
        with mock.patch(
            "game.combat.StandardShotResolver", wraps=StandardShotResolver
        ) as patched:
            self._fire(_weapon(name="ML", cluster=False))
        patched.assert_called_once()

    def test_cluster_weapon_uses_cluster_resolver(self):
        with mock.patch(
            "game.combat.ClusterShotResolver", wraps=ClusterShotResolver
        ) as patched:
            with _all_sixes():
                self._fire(_weapon(name="LRM20", cluster=True, num_shots=20,
                                   cluster_damage=5, damage=20))
        patched.assert_called_once()

    def test_ultra_double_tap_uses_ultra_resolver(self):
        ultra = _weapon(name="UAC10", cluster=False, num_shots=2, cluster_damage=10,
                        modifications={"weapon_type": "ULTRA"})
        with mock.patch(
            "game.combat.UltraShotResolver", wraps=UltraShotResolver
        ) as patched:
            with _all_sixes():
                self._fire(ultra, double_tap_flags=[True])
        patched.assert_called_once()

    def test_ultra_single_tap_uses_standard_resolver(self):
        ultra = _weapon(name="UAC10", cluster=False, num_shots=2, cluster_damage=10,
                        modifications={"weapon_type": "ULTRA"})
        with mock.patch(
            "game.combat.StandardShotResolver", wraps=StandardShotResolver
        ) as patched:
            with _all_sixes():
                self._fire(ultra, double_tap_flags=[False])
        patched.assert_called_once()

    def test_streak_uses_streak_resolver(self):
        streak = _weapon(name="SSRM6", cluster=False, num_shots=6, cluster_damage=2,
                         damage=12, modifications={"weapon_type": "STREAK"})
        with mock.patch(
            "game.combat.StreakShotResolver", wraps=StreakShotResolver
        ) as patched:
            with _all_sixes():
                self._fire(streak)
        patched.assert_called_once()


# ---------------------------------------------------------------------------
# Targeting Computer
# ---------------------------------------------------------------------------

class TargetingComputerTest(unittest.TestCase):
    """TC lowers target number by 1 for Standard and ULTRA weapons only."""

    def _fire(self, weapon, *, unit, distance=1, double_tap_flags=None):
        return _resolver(weapon).resolve_fire(
            unit, [weapon.name],
            pilot_gunnery_skill=4,
            distance_modifier=distance,
            double_tap_flags=double_tap_flags,
        )

    def test_tc_reduces_target_number_for_standard_weapon(self):
        unit_with_tc = _unit(attachments=[_attachment("TC")])
        weapon = _weapon(name="ML")
        result_no_tc = self._fire(weapon, unit=_unit())
        result_tc    = self._fire(weapon, unit=unit_with_tc)
        tn_no_tc = result_no_tc["shots"][0]["target_number"]
        tn_tc    = result_tc["shots"][0]["target_number"]
        self.assertEqual(tn_tc, tn_no_tc - 1)

    def test_ctc_also_reduces_target_number(self):
        unit_with_ctc = _unit(attachments=[_attachment("CTC")])
        weapon = _weapon(name="ML")
        result_no_tc = self._fire(weapon, unit=_unit())
        result_ctc   = self._fire(weapon, unit=unit_with_ctc)
        self.assertEqual(
            result_ctc["shots"][0]["target_number"],
            result_no_tc["shots"][0]["target_number"] - 1,
        )

    def test_tc_reduces_target_number_for_ultra_double_tap(self):
        unit_with_tc = _unit(attachments=[_attachment("TC")])
        ultra = _weapon(name="UAC10", cluster=False, num_shots=2, cluster_damage=10,
                        modifications={"weapon_type": "ULTRA"})
        result_no_tc = self._fire(ultra, unit=_unit(), double_tap_flags=[True])
        result_tc    = self._fire(ultra, unit=unit_with_tc, double_tap_flags=[True])
        tn_no_tc = result_no_tc["shots"][0]["target_number"]
        tn_tc    = result_tc["shots"][0]["target_number"]
        self.assertEqual(tn_tc, tn_no_tc - 1)

    def test_tc_does_not_affect_cluster_weapons(self):
        unit_with_tc = _unit(attachments=[_attachment("TC")])
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20,
                         cluster_damage=5, damage=20)
        result_no_tc = self._fire(weapon, unit=_unit())
        result_tc    = self._fire(weapon, unit=unit_with_tc)
        self.assertEqual(
            result_no_tc["shots"][0]["target_number"],
            result_tc["shots"][0]["target_number"],
        )

    def test_tc_does_not_affect_streak_weapons(self):
        unit_with_tc = _unit(attachments=[_attachment("TC")])
        streak = _weapon(name="SSRM6", cluster=False, num_shots=6, cluster_damage=2,
                         damage=12, modifications={"weapon_type": "STREAK"})
        result_no_tc = self._fire(streak, unit=_unit())
        result_tc    = self._fire(streak, unit=unit_with_tc)
        self.assertEqual(
            result_no_tc["shots"][0]["target_number"],
            result_tc["shots"][0]["target_number"],
        )

    def test_tc_is_safe_when_weapon_is_out_of_range(self):
        # target_number is None for out-of-range shots; must not raise TypeError.
        unit_with_tc = _unit(attachments=[_attachment("TC")])
        weapon = _weapon(name="ML", long_range=3)
        try:
            self._fire(weapon, unit=unit_with_tc, distance=99)
        except TypeError:
            self.fail("TC modifier raised TypeError on out-of-range shot")

    def test_no_tc_attachment_leaves_target_number_unchanged(self):
        unit_no_tc = _unit(attachments=[])
        weapon = _weapon(name="ML")
        result = self._fire(weapon, unit=unit_no_tc)
        # gunnery 4 + short range 0 = 4
        self.assertEqual(result["shots"][0]["target_number"], 4)

    def test_ultra_single_tap_also_gets_tc_bonus(self):
        """Single-tap ULTRA routes to StandardShotResolver; TC still applies."""
        unit_with_tc = _unit(attachments=[_attachment("TC")])
        ultra = _weapon(name="UAC10", cluster=False, num_shots=2, cluster_damage=10,
                        modifications={"weapon_type": "ULTRA"})
        result_no_tc = self._fire(ultra, unit=_unit(), double_tap_flags=[False])
        result_tc    = self._fire(ultra, unit=unit_with_tc, double_tap_flags=[False])
        self.assertEqual(
            result_tc["shots"][0]["target_number"],
            result_no_tc["shots"][0]["target_number"] - 1,
        )


if __name__ == "__main__":
    unittest.main()
