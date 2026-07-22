"""Unit tests for :mod:`combat`.

``combat`` uses a local ``from tables import ...``, so ``backend/game`` must be
on ``sys.path``. The insert below handles that regardless of where the tests are
run from::

    python -m unittest discover backend/tests -v
    # or, from the repo root:
    python -m pytest backend/tests/test_combat.py

The dice rollers (``roll_1d6``) are monkeypatched in most tests so results are
deterministic instead of relying on ``random``.
"""

import os
import sys
import unittest
from unittest import mock

_GAME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")
sys.path.insert(0, os.path.abspath(_GAME_DIR))

import combat
from combat import (
    CombatResolver,
    DiceRollsResults,
    WeaponShot,
    roll_1d6,
    roll_2d6,
)


def _weapon(name="Medium Laser", count=1, damage=5, heat=3, location="RA"):
    """Build a weapon dict of the shape ``resolve_fire`` expects."""
    return {
        "name": name,
        "count": count,
        "damage": damage,
        "heat": heat,
        "location": location,
    }


class FixedDice:
    """Context-managerish helper: patch roll_1d6 to yield a fixed sequence.

    Values are consumed in call order and cycle if exhausted, so a single
    value (e.g. ``6``) makes every die deterministic.
    """

    def __init__(self, *values):
        self.values = list(values)
        self.calls = 0

    def __call__(self):
        v = self.values[self.calls % len(self.values)]
        self.calls += 1
        return v


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

    def test_stores_all_values(self):
        dice = DiceRollsResults(to_hit_1=1, to_hit_2=2, location_1=3, location_2=4)
        self.assertEqual((dice.to_hit_1, dice.to_hit_2), (1, 2))
        self.assertEqual((dice.location_1, dice.location_2), (3, 4))


class WeaponShotTest(unittest.TestCase):
    def _shot(self, to_hit, target_number, facing="Front/Rear", loc=(4, 4)):
        dice = DiceRollsResults(
            to_hit_1=to_hit[0],
            to_hit_2=to_hit[1],
            location_1=loc[0],
            location_2=loc[1],
        )
        return WeaponShot(
            weapon="AC/20",
            location="RT",
            target_number=target_number,
            target_facing=facing,
            dice=dice,
        )

    def test_roll_is_sum_of_to_hit_dice(self):
        shot = self._shot(to_hit=(5, 6), target_number=7)
        self.assertEqual(shot.roll, 11)

    def test_hit_when_roll_meets_target_number(self):
        shot = self._shot(to_hit=(3, 4), target_number=7)  # roll == 7
        self.assertTrue(shot.hit)

    def test_miss_when_roll_below_target_number(self):
        shot = self._shot(to_hit=(3, 3), target_number=7)  # roll == 6
        self.assertFalse(shot.hit)
        self.assertEqual(shot.hit_location, "Miss")

    def test_hit_location_from_front_rear_table(self):
        # location roll 4 + 4 == 8 -> "Left Torso" in FRONT_REAR_LOCATION_TABLE
        shot = self._shot(to_hit=(6, 6), target_number=7, facing="Front/Rear", loc=(4, 4))
        self.assertTrue(shot.hit)
        self.assertEqual(shot.hit_location, combat.FRONT_REAR_LOCATION_TABLE[8])

    def test_hit_location_from_right_side_table(self):
        shot = self._shot(to_hit=(6, 6), target_number=7, facing="Right Side", loc=(6, 6))
        self.assertEqual(shot.hit_location, combat.RIGHT_SIDE_LOCATION_TABLE[12])

    def test_hit_location_from_left_side_table(self):
        shot = self._shot(to_hit=(6, 6), target_number=7, facing="Left Side", loc=(1, 1))
        self.assertEqual(shot.hit_location, combat.LEFT_SIDE_LOCATION_TABLE[2])


class ResolveFireTest(unittest.TestCase):
    def setUp(self):
        self.resolver = CombatResolver()

    # -- guaranteed hit --------------------------------------------------

    def test_guaranteed_hit_applies_full_damage(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6)):  # every roll -> 12
            result = self.resolver.resolve_fire(
                "Atlas", [_weapon(damage=20, heat=7, count=1)]
            )
        self.assertEqual(result["hits"], 1)
        self.assertEqual(result["misses"], 0)
        self.assertEqual(result["total_damage"], 20)
        self.assertTrue(result["shots"][0]["hit"])

    # -- guaranteed miss -------------------------------------------------

    def test_guaranteed_miss_deals_no_damage_but_accrues_heat(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(1)):  # every roll -> 2
            result = self.resolver.resolve_fire(
                "Atlas", [_weapon(damage=20, heat=7, count=1)]
            )
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["misses"], 1)
        self.assertEqual(result["total_damage"], 0)
        self.assertEqual(result["total_heat"], 7)  # heat accrues even on a miss
        self.assertEqual(result["shots"][0]["hit_location"], "Miss")

    # -- shot count ------------------------------------------------------

    def test_weapon_count_produces_that_many_shots(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6)):
            result = self.resolver.resolve_fire("Atlas", [_weapon(count=4, damage=1)])
        self.assertEqual(len(result["shots"]), 4)
        self.assertEqual(result["total_damage"], 4)

    def test_count_below_one_still_fires_once(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6)):
            result = self.resolver.resolve_fire("Atlas", [_weapon(count=0, damage=3)])
        self.assertEqual(len(result["shots"]), 1)

    def test_multiple_weapons_are_all_resolved(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6)):
            result = self.resolver.resolve_fire(
                "Atlas",
                [_weapon(name="LRM", count=2, damage=1), _weapon(name="AC", count=1, damage=5)],
            )
        self.assertEqual(len(result["shots"]), 3)
        self.assertEqual(result["total_damage"], 7)

    # -- movement modifier -----------------------------------------------

    def test_movement_modifier_raises_target_number(self):
        result = self.resolver.resolve_fire(
            "Atlas", [_weapon()], target_movement_modifier=3
        )
        self.assertEqual(
            result["shots"][0]["target_number"],
            CombatResolver.BASE_TARGET_NUMBER + 3,
        )
        self.assertEqual(result["target_movement_modifier"], 3)

    def test_modifier_can_make_a_roll_that_would_hit_at_base_miss(self):
        # roll of 7 hits at TN 7 but misses at TN 10.
        with mock.patch.object(combat, "roll_1d6", FixedDice(3, 4)):
            result = self.resolver.resolve_fire(
                "Atlas", [_weapon()], target_movement_modifier=3
            )
        self.assertEqual(result["hits"], 0)

    # -- defaults / missing keys ----------------------------------------

    def test_missing_optional_keys_use_defaults(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6)):
            result = self.resolver.resolve_fire("Atlas", [{}])  # no name/damage/heat/count
        self.assertEqual(len(result["shots"]), 1)
        self.assertEqual(result["shots"][0]["weapon"], "Unknown")
        self.assertEqual(result["total_damage"], 0)
        self.assertEqual(result["total_heat"], 0)

    def test_none_damage_and_heat_are_treated_as_zero(self):
        with mock.patch.object(combat, "roll_1d6", FixedDice(6)):
            result = self.resolver.resolve_fire(
                "Atlas", [_weapon(damage=None, heat=None)]
            )
        self.assertEqual(result["total_damage"], 0)
        self.assertEqual(result["total_heat"], 0)

    # -- return shape ----------------------------------------------------

    def test_result_contains_expected_keys(self):
        result = self.resolver.resolve_fire("Atlas", [_weapon()], target_name="Locust")
        for key in (
            "attacker",
            "target",
            "target_movement_modifier",
            "shots",
            "hits",
            "misses",
            "total_damage",
            "total_heat",
        ):
            self.assertIn(key, result)
        self.assertEqual(result["attacker"], "Atlas")
        self.assertEqual(result["target"], "Locust")

    def test_hits_plus_misses_equals_shot_count(self):
        result = self.resolver.resolve_fire("Atlas", [_weapon(count=5)])
        self.assertEqual(result["hits"] + result["misses"], len(result["shots"]))

    def test_no_weapons_yields_empty_result(self):
        result = self.resolver.resolve_fire("Atlas", [])
        self.assertEqual(result["shots"], [])
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["total_damage"], 0)


if __name__ == "__main__":
    unittest.main()
