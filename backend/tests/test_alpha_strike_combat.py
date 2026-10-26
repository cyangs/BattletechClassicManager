"""TDD spec for AlphaStrikeCombatResolver — the to-hit assembly + orchestration
layer for Alpha Strike (parallel to Classic's CombatResolver).

It computes the GATOR-equivalent to-hit number:

    target_number = pilot_skill + attacker_move_mod + target_tmm
                    + range_modifier + other

then delegates the dice to the step-2 AlphaStrikeResolver. Range brackets by
distance (inches): Short 0-6 (+0), Medium 6-24 (+2), Long 24-42 (+4); beyond
long is out of range (automatic miss).

Run just this file::

    python -m unittest discover backend/tests -p test_alpha_strike_combat.py -v
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game.alpha_strike import AlphaStrikeCombatResolver  # noqa: E402 (RED)
from game.alpha_strike.models import RangeBand


def _card(short=4, medium=4, long=3, armor=9, structure=6, tmm=0,
          short_range=6, medium_range=24, long_range=42):
    """Stand-in for an AlphaStrikeCard with AS range brackets (inches)."""
    return types.SimpleNamespace(
        damage_short=short, damage_medium=medium, damage_long=long,
        armor=armor, structure=structure, overheat=0, tmm=tmm,
        short_range=short_range, medium_range=medium_range, long_range=long_range,
    )


def _all_sixes():
    return mock.patch("random.randint", side_effect=lambda a, b: 6)


def _resolver(**overrides):
    defaults = dict(
        attacker_card=_card(),
        target_card=_card(tmm=0),
        pilot_skill=4,
        distance=10,                 # medium bracket
        attacker_movement_modifier=0,
        additional_modifier=0,
        damage_mode="standard",
        target_armor=9,
        target_structure=6,
    )
    defaults.update(overrides)
    return AlphaStrikeCombatResolver(**defaults)


class RangeBracketTest(unittest.TestCase):
    def test_short_bracket(self):
        with _all_sixes():
            r = _resolver(distance=5).resolve()
        self.assertEqual(r.range_band, RangeBand.SHORT)

    def test_medium_bracket(self):
        with _all_sixes():
            r = _resolver(distance=20).resolve()
        self.assertEqual(r.range_band, RangeBand.MEDIUM)

    def test_long_bracket(self):
        with _all_sixes():
            r = _resolver(distance=40).resolve()
        self.assertEqual(r.range_band, RangeBand.LONG)

    def test_beyond_long_is_out_of_range(self):
        r = _resolver(distance=99).resolve()
        self.assertIsNone(r.range_band)
        self.assertIsNone(r.target_number)
        self.assertFalse(r.hit)
        self.assertEqual(r.damage_dealt, 0)


class ToHitAssemblyTest(unittest.TestCase):
    def test_gator_components_sum_into_target_number(self):
        # skill 4 + atk-move 1 + target tmm 2 + range(medium +2) + other 1 = 10
        with _all_sixes():
            r = _resolver(
                pilot_skill=4,
                attacker_movement_modifier=1,
                target_card=_card(tmm=2),
                distance=20,                 # medium -> +2
                additional_modifier=1,
            ).resolve()
        self.assertEqual(r.target_number, 4 + 1 + 2 + 2 + 1)

    def test_short_range_adds_zero(self):
        with _all_sixes():
            r = _resolver(pilot_skill=4, distance=5).resolve()   # short -> +0
        self.assertEqual(r.target_number, 4)

    def test_long_range_adds_four(self):
        with _all_sixes():
            r = _resolver(pilot_skill=3, distance=40).resolve()  # long -> +4
        self.assertEqual(r.target_number, 3 + 4)


class DelegationTest(unittest.TestCase):
    def test_standard_mode_full_bracket_on_hit(self):
        # Medium bracket damage 4; guaranteed hit (all sixes).
        with _all_sixes():
            r = _resolver(distance=20, damage_mode="standard").resolve()
        self.assertTrue(r.hit)
        self.assertEqual(r.mode, "standard")
        self.assertEqual(r.damage_dealt, 4)
        self.assertEqual(len(r.rolls), 1)

    def test_variable_mode_rolls_per_point(self):
        # Medium bracket damage 4 -> four 2d6 rolls in variable mode.
        with _all_sixes():
            r = _resolver(distance=20, damage_mode="variable").resolve()
        self.assertEqual(r.mode, "variable")
        self.assertEqual(len(r.rolls), 4)
        self.assertEqual(r.damage_dealt, 4)

    def test_damage_applied_to_target_defense(self):
        with _all_sixes():
            r = _resolver(distance=20, target_armor=9, target_structure=6).resolve()
        self.assertEqual(r.target_armor_before, 9)
        self.assertEqual(r.target_armor_after, 5)        # 4 dmg off armor
        self.assertEqual(r.target_structure_after, 6)

    def test_names_passed_through(self):
        with _all_sixes():
            r = _resolver(
                distance=20, attacker_name="Turkina", target_name="Atlas",
            ).resolve()
        self.assertEqual(r.attacker, "Turkina")
        self.assertEqual(r.target, "Atlas")


if __name__ == "__main__":
    unittest.main()
