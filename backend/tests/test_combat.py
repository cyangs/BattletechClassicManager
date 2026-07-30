"""Unit tests for :mod:`combat`.

``combat`` uses local package imports (``game.tables``, ``database.dao...``), so
``backend`` must be on ``sys.path``. The insert below handles that regardless of
where the tests are run from::

    python -m unittest discover backend/tests -v
    # or, from the repo root:
    python -m pytest backend/tests/test_combat.py

The dice roller (``roll_1d6``) is monkeypatched in most tests so results are
deterministic instead of relying on ``random``. The database is replaced with an
in-memory ``FakeWeaponRepository`` so no real DB connection is required.
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game import combat
from game.combat import (
    CombatResolver,
    DiceRollsResults,
    RangeBand,
    WeaponShot,
    roll_1d6,
    roll_2d6,
)


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
):
    """Build a stand-in for a ``Weapon`` ORM row (attribute access)."""
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
    """Callable that yields a fixed, cycling sequence of die values."""

    def __init__(self, *values):
        self.values = list(values)
        self.calls = 0

    def __call__(self):
        v = self.values[self.calls % len(self.values)]
        self.calls += 1
        return v


def _all_sixes():
    """Patch roll_1d6 so every 1d6 is a 6 (to-hit 12, location 12)."""
    return mock.patch.object(combat, "roll_1d6", FixedDice(6))


def _all_ones():
    """Patch roll_1d6 so every 1d6 is a 1 (to-hit 2 -> guaranteed miss)."""
    return mock.patch.object(combat, "roll_1d6", FixedDice(1))


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


class WeaponShotTest(unittest.TestCase):
    def _shot(self, target_number, facing="Front/Rear", range_band="SHORT", damage=5):
        return WeaponShot(
            weapon="AC/20",
            location="RT",
            target_number=target_number,
            target_facing=facing,
            range_band=range_band,
            damage=damage,
        )

    def test_out_of_range_is_an_automatic_miss(self):
        shot = self._shot(target_number=None)
        self.assertFalse(shot.hit)
        self.assertEqual(shot.roll, 0)
        self.assertEqual(shot.damage, 0)
        self.assertEqual(shot.hit_location, "Target Out of Range")

    def test_hit_keeps_damage_and_sets_location(self):
        with _all_sixes():  # to-hit 12 >= 7, location roll 12 -> "Head"
            shot = self._shot(target_number=7, damage=20)
        self.assertTrue(shot.hit)
        self.assertEqual(shot.roll, 12)
        self.assertEqual(shot.damage, 20)
        self.assertEqual(shot.hit_location, combat.FRONT_REAR_LOCATION_TABLE[12])

    def test_miss_zeroes_damage(self):
        with _all_ones():  # to-hit 2 < 7
            shot = self._shot(target_number=7, damage=20)
        self.assertFalse(shot.hit)
        self.assertEqual(shot.damage, 0)
        self.assertEqual(shot.hit_location, "Miss")

    def test_left_side_facing_uses_left_table(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6, 6, 1, 1)):
            # to-hit dice 6+6=12 (hit), location dice 1+1=2
            shot = self._shot(target_number=7, facing="Left Side")
        self.assertEqual(shot.hit_location, combat.LEFT_SIDE_LOCATION_TABLE[2])

    def test_right_side_facing_uses_right_table(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6, 6, 3, 3)):
            # to-hit 12 (hit), location 3+3=6
            shot = self._shot(target_number=7, facing="Right Side")
        self.assertEqual(shot.hit_location, combat.RIGHT_SIDE_LOCATION_TABLE[6])


class ResolveFireTest(unittest.TestCase):
    # -- database lookup -------------------------------------------------

    def test_looks_weapon_up_by_name_and_uses_db_stats(self):
        resolver = _resolver(_weapon(name="AC20", full_name="AC/20", damage=20, heat=7))
        with _all_sixes():
            result = resolver.resolve_fire("Atlas", ["AC20"], pilot_gunnery_skill=4)
        shot = result["shots"][0]
        self.assertEqual(shot["weapon"], "AC/20")  # display name from the DB record
        self.assertEqual(shot["damage"], 20)
        self.assertEqual(result["total_heat"], 7)

    def test_unknown_weapon_name_is_reported_not_dropped_silently(self):
        resolver = _resolver(_weapon(name="AC20"))
        result = resolver.resolve_fire("Atlas", ["AC20", "Nope"], pilot_gunnery_skill=4)
        self.assertEqual(result["unresolved_weapons"], ["Nope"])
        self.assertEqual(len(result["shots"]), 1)

    def test_repeated_lookup_is_cached_single_db_hit(self):
        repo = FakeWeaponRepository(_weapon(name="ML"))
        repo.fetch_weapon_by_name = mock.Mock(side_effect=repo.fetch_weapon_by_name)
        CombatResolver(repo).resolve_fire("Atlas", ["ML", "ML", "ML"], pilot_gunnery_skill=4)
        self.assertEqual(repo.fetch_weapon_by_name.call_count, 1)

    # -- guaranteed hit / miss ------------------------------------------

    def test_guaranteed_hit_applies_full_damage(self):
        resolver = _resolver(_weapon(name="ML", damage=20))
        with _all_sixes():
            result = resolver.resolve_fire("Atlas", ["ML"], pilot_gunnery_skill=4)
        self.assertEqual(result["hits"], 1)
        self.assertEqual(result["misses"], 0)
        self.assertEqual(result["total_damage"], 20)

    def test_guaranteed_miss_deals_no_damage_but_accrues_heat(self):
        resolver = _resolver(_weapon(name="ML", damage=20, heat=7))
        with _all_ones():
            result = resolver.resolve_fire("Atlas", ["ML"], pilot_gunnery_skill=4)
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["total_damage"], 0)
        self.assertEqual(result["total_heat"], 7)  # heat accrues even on a miss
        self.assertEqual(result["shots"][0]["hit_location"], "Miss")

    # -- shot count (name repeated per shot) ----------------------------

    def test_repeated_name_fires_once_per_entry(self):
        resolver = _resolver(_weapon(name="ML", damage=1))
        with _all_sixes():
            result = resolver.resolve_fire("Atlas", ["ML", "ML", "ML", "ML"], pilot_gunnery_skill=4)
        self.assertEqual(len(result["shots"]), 4)
        self.assertEqual(result["total_damage"], 4)

    # -- target-number composition --------------------------------------

    def test_target_number_is_gunnery_plus_range_bracket(self):
        resolver = _resolver(_weapon(name="ML", short_range=3, medium_range=6, long_range=9))
        # distance 5 is in the medium bracket (short 3 < 5 <= medium 6) -> +2
        result = resolver.resolve_fire("Atlas", ["ML"], pilot_gunnery_skill=4, distance_modifier=5)
        self.assertEqual(result["shots"][0]["target_number"], 4 + 2)
        self.assertEqual(result["shots"][0]["range_band"], "MEDIUM")

    def test_modifiers_stack_into_target_number(self):
        resolver = _resolver(_weapon(name="ML"))
        # gunnery 3 + movement 2 + terrain 1 + partial cover 1 + short bracket 0
        result = resolver.resolve_fire(
            "Atlas", ["ML"], pilot_gunnery_skill=3, distance_modifier=2,
            target_movement_modifier=2, intervening_terrain=1, partial_cover=True,
        )
        self.assertEqual(result["shots"][0]["target_number"], 3 + 2 + 1 + 1)
        self.assertEqual(result["shots"][0]["range_band"], "SHORT")

    def test_target_number_does_not_compound_across_shots(self):
        resolver = _resolver(_weapon(name="ML", short_range=3, medium_range=6, long_range=9))
        with _all_sixes():
            result = resolver.resolve_fire(
                "Atlas", ["ML", "ML"], pilot_gunnery_skill=4, distance_modifier=8  # long
            )
        tns = {s["target_number"] for s in result["shots"]}
        self.assertEqual(tns, {4 + 4})

    # -- out of range ----------------------------------------------------

    def test_beyond_long_range_is_out_of_range(self):
        resolver = _resolver(_weapon(name="ML", long_range=9))
        result = resolver.resolve_fire("Atlas", ["ML"], pilot_gunnery_skill=4, distance_modifier=15)
        shot = result["shots"][0]
        self.assertIsNone(shot["target_number"])
        self.assertFalse(shot["hit"])
        self.assertEqual(shot["damage"], 0)
        self.assertEqual(shot["hit_location"], "Target Out of Range")
        self.assertEqual(result["hits"], 0)

    # -- variable damage -------------------------------------------------

    def test_variable_damage_uses_band_specific_value(self):
        weapon = _weapon(
            name="Ultra", damage=0, variable_damage=True,
            short_range_damage=10, medium_range_damage=7, long_range_damage=4,
        )
        with _all_sixes():  # guaranteed hit so damage is applied
            result = _resolver(weapon).resolve_fire(
                "Atlas", ["Ultra"], pilot_gunnery_skill=4, distance_modifier=8  # long bracket
            )
        self.assertEqual(result["shots"][0]["damage"], 4)

    def test_variable_damage_falls_back_to_flat_when_band_null(self):
        weapon = _weapon(name="Ultra", damage=6, variable_damage=True, short_range_damage=None)
        with _all_sixes():
            result = _resolver(weapon).resolve_fire(
                "Atlas", ["Ultra"], pilot_gunnery_skill=4, distance_modifier=1  # short bracket
            )
        self.assertEqual(result["shots"][0]["damage"], 6)

    # -- return shape ----------------------------------------------------

    def test_result_contains_expected_keys(self):
        resolver = _resolver(_weapon(name="ML"))
        result = resolver.resolve_fire("Atlas", ["ML"], pilot_gunnery_skill=4, target_name="Locust")
        for key in (
            "attacker", "target", "target_movement_modifier", "shots",
            "hits", "misses", "total_damage", "total_heat", "unresolved_weapons",
        ):
            self.assertIn(key, result)
        self.assertEqual(result["attacker"], "Atlas")
        self.assertEqual(result["target"], "Locust")

    def test_hits_plus_misses_equals_shot_count(self):
        resolver = _resolver(_weapon(name="ML"))
        result = resolver.resolve_fire("Atlas", ["ML"] * 5, pilot_gunnery_skill=4)
        self.assertEqual(result["hits"] + result["misses"], len(result["shots"]))

    def test_no_weapons_yields_empty_result(self):
        result = _resolver().resolve_fire("Atlas", [], pilot_gunnery_skill=4)
        self.assertEqual(result["shots"], [])
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["total_damage"], 0)


if __name__ == "__main__":
    unittest.main()
