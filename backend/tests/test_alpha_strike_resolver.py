"""TDD spec for the Alpha Strike combat calculator.

Alpha Strike is NOT the Classic per-weapon model. A unit has three bracket
damage values (S/M/L, small integers) and flat armor/structure pip tracks.
An attack is a 2D6 to-hit against a target number, in one of two modes:

  * standard  — all-or-nothing: hit -> full bracket damage, miss -> 0.
  * variable  — roll one 2D6 PER POINT of bracket damage, each against the SAME
                target number; damage dealt = how many met it (0..bracket).

Damage subtracts from armor first, overflowing into structure (floored at 0).
No hit locations, clusters, or crits. ``target_number`` of None = out of range
(automatic miss), mirroring the Classic resolver convention.

The resolver is pure logic (dice via random.randint, patched in tests) — it
takes an already-computed to-hit target number, like the Classic resolvers.

Run just this file::

    python -m unittest discover backend/tests -p test_alpha_strike_resolver.py -v
"""

import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game.alpha_strike import AlphaStrikeResolver, AsAttackResult, serialize_as_attack  # noqa: E402 (RED)
from game.alpha_strike.models import RangeBand  # noqa: E402


def _card(short=4, medium=4, long=3, armor=9, structure=6):
    """Stand-in for an AlphaStrikeCard (attribute access only)."""
    return types.SimpleNamespace(
        damage_short=short, damage_medium=medium, damage_long=long,
        armor=armor, structure=structure, overheat=0,
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


def _all_sixes():
    return mock.patch("random.randint", side_effect=lambda a, b: 6)


def _all_ones():
    return mock.patch("random.randint", side_effect=lambda a, b: 1)


# ---------------------------------------------------------------------------
# Standard (all-or-nothing) mode
# ---------------------------------------------------------------------------

class StandardModeTest(unittest.TestCase):
    def _resolve(self, *, range_band, target_number, armor=9, structure=6):
        return AlphaStrikeResolver(
            card=_card(short=4, medium=4, long=3, armor=armor, structure=structure),
            range_band=range_band,
            target_number=target_number,
            damage_mode="standard",
            target_armor=armor,
            target_structure=structure,
        ).resolve()

    def test_hit_deals_full_bracket_damage(self):
        # 6+6=12 >= 7 -> hit. Medium bracket damage is 4.
        with _all_sixes():
            r = self._resolve(range_band=RangeBand.MEDIUM, target_number=7)
        self.assertTrue(r.hit)
        self.assertEqual(r.bracket_damage, 4)
        self.assertEqual(r.damage_dealt, 4)
        self.assertEqual(len(r.rolls), 1)                 # standard = one 2d6

    def test_miss_deals_zero(self):
        with _all_ones():   # 1+1=2 < 7
            r = self._resolve(range_band=RangeBand.MEDIUM, target_number=7)
        self.assertFalse(r.hit)
        self.assertEqual(r.damage_dealt, 0)

    def test_long_bracket_used_at_long_range(self):
        with _all_sixes():
            r = self._resolve(range_band=RangeBand.LONG, target_number=7)
        self.assertEqual(r.bracket_damage, 3)             # long damage
        self.assertEqual(r.damage_dealt, 3)

    def test_out_of_range_is_automatic_miss(self):
        r = self._resolve(range_band=None, target_number=None)
        self.assertFalse(r.hit)
        self.assertEqual(r.damage_dealt, 0)
        self.assertEqual(r.rolls, [])


# ---------------------------------------------------------------------------
# Variable mode (optional rule)
# ---------------------------------------------------------------------------

class VariableModeTest(unittest.TestCase):
    def _resolve(self, *, dice_values, range_band=RangeBand.MEDIUM, target_number=7,
                 armor=9, structure=6, card=None):
        with _fixed(*dice_values):
            return AlphaStrikeResolver(
                card=card or _card(armor=armor, structure=structure),
                range_band=range_band,
                target_number=target_number,
                damage_mode="variable",
                target_armor=armor,
                target_structure=structure,
            ).resolve()

    def test_rolls_one_2d6_per_point_of_bracket_damage(self):
        # Medium damage 4 -> four 2d6 rolls. All sixes (12) -> all 4 land.
        r = self._resolve(dice_values=[6, 6])  # cycles to all 6s
        self.assertEqual(r.bracket_damage, 4)
        self.assertEqual(len(r.rolls), 4)                 # one per point
        self.assertEqual(r.damage_dealt, 4)
        self.assertTrue(r.hit)

    def test_roll_pairs_expose_individual_dice(self):
        # Each entry is the [d1, d2] pair; rolls is the derived total.
        # Four rolls of 3+4=7 (medium damage 4).
        r = self._resolve(dice_values=[3, 4])   # cycles 3,4,3,4,...
        self.assertEqual(len(r.roll_pairs), 4)
        self.assertTrue(all(pair == [3, 4] for pair in r.roll_pairs))
        self.assertEqual(r.rolls, [7, 7, 7, 7])  # totals derived from the pairs

    def test_partial_landed_damage(self):
        # Four rolls vs target 7: make exactly 2 of them meet it.
        # roll1 = 6+6=12 (hit), roll2 = 1+1=2 (miss), roll3 = 4+4=8 (hit),
        # roll4 = 1+2=3 (miss).  -> 2 damage.
        r = self._resolve(dice_values=[6, 6, 1, 1, 4, 4, 1, 2])
        self.assertEqual(r.damage_dealt, 2)
        self.assertTrue(r.hit)                             # at least one landed

    def test_all_dice_miss_is_zero_and_not_a_hit(self):
        r = self._resolve(dice_values=[1, 1])              # every roll a 2
        self.assertEqual(r.damage_dealt, 0)
        self.assertFalse(r.hit)

    def test_zero_bracket_damage_rolls_nothing(self):
        # A unit with 0 damage in this bracket rolls no dice, deals nothing.
        card = _card(short=0, medium=0, long=0)
        r = self._resolve(dice_values=[6, 6], card=card)
        self.assertEqual(r.bracket_damage, 0)
        self.assertEqual(r.rolls, [])
        self.assertEqual(r.damage_dealt, 0)

    def test_variable_out_of_range_auto_miss(self):
        r = self._resolve(dice_values=[6, 6], range_band=None, target_number=None)
        self.assertFalse(r.hit)
        self.assertEqual(r.damage_dealt, 0)
        self.assertEqual(r.rolls, [])


# ---------------------------------------------------------------------------
# Damage application to armor / structure
# ---------------------------------------------------------------------------

class DamageApplicationTest(unittest.TestCase):
    def _resolve(self, *, target_armor, target_structure, bracket=4):
        with _all_sixes():   # guaranteed full hit in standard mode
            return AlphaStrikeResolver(
                card=_card(medium=bracket, armor=target_armor, structure=target_structure),
                range_band=RangeBand.MEDIUM,
                target_number=7,
                damage_mode="standard",
                target_armor=target_armor,
                target_structure=target_structure,
            ).resolve()

    def test_damage_comes_off_armor_first(self):
        r = self._resolve(target_armor=9, target_structure=6)   # 4 dmg
        self.assertEqual(r.target_armor_before, 9)
        self.assertEqual(r.target_armor_after, 5)
        self.assertEqual(r.target_structure_before, 6)
        self.assertEqual(r.target_structure_after, 6)           # untouched

    def test_overflow_into_structure(self):
        # 4 damage vs 2 armor -> 2 removes armor, 2 overflows into structure.
        r = self._resolve(target_armor=2, target_structure=6)
        self.assertEqual(r.target_armor_after, 0)
        self.assertEqual(r.target_structure_after, 4)

    def test_damage_floored_at_zero_structure(self):
        # 4 damage vs 1 armor + 1 structure -> both to 0, no negative.
        r = self._resolve(target_armor=1, target_structure=1)
        self.assertEqual(r.target_armor_after, 0)
        self.assertEqual(r.target_structure_after, 0)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class SerializeTest(unittest.TestCase):
    def test_serialize_is_json_safe(self):
        import json
        with _all_sixes():
            r = AlphaStrikeResolver(
                card=_card(), range_band=RangeBand.SHORT, target_number=7,
                damage_mode="standard", target_armor=9, target_structure=6,
            ).resolve()
        d = serialize_as_attack(r)
        self.assertEqual(d["range_band"], "SHORT")        # enum -> label
        self.assertEqual(d["mode"], "standard")
        json.dumps(d)                                     # must not raise


if __name__ == "__main__":
    unittest.main()
