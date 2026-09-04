"""Unit tests for :mod:`combat`.

``combat`` uses local package imports (``game.tables``, ``database.dao...``), so
``backend`` must be on ``sys.path``. The insert below handles that regardless of
where the tests are run from::

    python -m unittest discover backend/tests -v
    # or, from the repo root:
    python -m pytest backend/tests/test_combat.py

The dice roller (``roll_1d6``) lives in :mod:`game.fire_calculations` and is
monkeypatched there in most tests so results are deterministic instead of
relying on ``random``. The database is replaced with an in-memory
``FakeWeaponRepository`` so no real DB connection is required.
"""

import json
import os
import sys
import types
import unittest
from unittest import mock

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from game import fire_calculations
from game.combat import (
    CombatResolver,
    DiceRollsResults,
    FireCalculations,
    RangeBand,
    WeaponShot,
    roll_1d6,
    roll_2d6,
    serialize_shot,
)
from game.tables import (
    FRONT_REAR_LOCATION_TABLE,
    LEFT_SIDE_LOCATION_TABLE,
    RIGHT_SIDE_LOCATION_TABLE,
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
        short_range_modifier=None,
        medium_range_modifier=None,
        long_range_modifier=None,
        num_shots=None,
        cluster_damage=None,
        modifications=None,
):
    """Build a stand-in for a ``Weapon`` ORM row (attribute access).

    ``has_range_modifiers`` mirrors the real model's property so pulse-style
    weapons exercise the range-modifier branch in ``WeaponShot``.
    """
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
        has_range_modifiers=any(
            m is not None
            for m in (short_range_modifier, medium_range_modifier, long_range_modifier)
        ),
    )


def _unit(name="Atlas"):
    """Stand-in for a ``SessionMech`` firing unit (``resolve_fire`` reads
    ``unit.master_mech.name`` for the result's attacker label)."""
    return types.SimpleNamespace(master_mech=types.SimpleNamespace(name=name))


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
    return mock.patch.object(fire_calculations, "roll_1d6", FixedDice(6))


def _all_ones():
    """Patch roll_1d6 so every 1d6 is a 1 (to-hit 2 -> guaranteed miss)."""
    return mock.patch.object(fire_calculations, "roll_1d6", FixedDice(1))


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


class FireCalculationsTest(unittest.TestCase):
    def _shot(self, target_number, facing="Front/Rear", range_band=RangeBand.SHORT, damage=5):
        # Damage is derived from the weapon record on a hit, so the requested
        # ``damage`` is baked into the stand-in weapon.
        return FireCalculations(
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

    def test_hit_keeps_damage_and_sets_location(self):
        with _all_sixes():  # to-hit 12 >= 7, location roll 12 -> "Head"
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
        with mock.patch.object(fire_calculations, "roll_1d6", FixedDice(6, 6, 1, 4)):
            # to-hit dice 6+6=12 (hit), location dice 1+4=5 (not a 2, so no crit)
            shot = self._shot(target_number=7, facing="Left Side")
        self.assertEqual(shot.hit_location, LEFT_SIDE_LOCATION_TABLE[5])

    def test_right_side_facing_uses_right_table(self):
        with mock.patch.object(fire_calculations, "roll_1d6", FixedDice(6, 6, 3, 3)):
            # to-hit 12 (hit), location 3+3=6
            shot = self._shot(target_number=7, facing="Right Side")
        self.assertEqual(shot.hit_location, RIGHT_SIDE_LOCATION_TABLE[6])

    def test_weapon_range_modifier_is_applied_per_band(self):
        # Variable pulse laser: -3 short, -2 medium, -1 long. The band-specific
        # (signed) modifier is added to the incoming target number.
        weapon = _weapon(name="Pulse", short_range_modifier=-3,
                         medium_range_modifier=-2, long_range_modifier=-1)
        expected_by_band = {
            RangeBand.SHORT: 10 - 3,
            RangeBand.MEDIUM: 10 - 2,
            RangeBand.LONG: 10 - 1,
        }
        for band, expected in expected_by_band.items():
            shot = FireCalculations(
                weapon=weapon, target_number=10,
                target_facing="Front/Rear", range_band=band,
            ).resolve()
            self.assertEqual(shot.target_number, expected, band)

    def test_no_range_modifier_leaves_target_number_unchanged(self):
        weapon = _weapon(name="ML")  # no per-band modifiers defined
        shot = FireCalculations(
            weapon=weapon, target_number=7,
            target_facing="Front/Rear", range_band=RangeBand.SHORT,
        ).resolve()
        self.assertEqual(shot.target_number, 7)

    def test_serialize_shot_is_json_safe(self):
        # ``weapon`` (an ORM object) and ``range_band`` (an enum) must flatten to
        # JSON-friendly values for the API response.
        with _all_sixes():
            shot = FireCalculations(
                weapon=_weapon(name="ML", full_name="Medium Laser", damage=5),
                target_number=7,
                target_facing="Front/Rear",
                range_band=RangeBand.MEDIUM,
            ).resolve()
        d = serialize_shot(shot)
        self.assertEqual(d["weapon"], "Medium Laser")  # display name, not the object
        self.assertEqual(d["range_band"], "MEDIUM")  # enum label, not the enum
        self.assertEqual(sorted(d.keys()), [
            "all_rolls", "cluster_hits", "cluster_hits_landed", "cluster_roll",
            "critical_hit", "damage", "hit", "hit_location",
            "range_band", "roll", "target_facing", "target_number", "weapon",
        ])
        json.dumps(d)  # must not raise

    def test_cluster_weapon_splits_damage_across_locations(self):
        # LRM 20 (cluster, cluster_damage 5). Forced dice: to-hit 6+6=12 (hit),
        # cluster roll 4+5=9 -> 16 points on the size-20 table, split 5/5/5/1
        # across four independently-rolled locations (3+4=7 -> Center Torso).
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20, cluster_damage=5, damage=20)
        dice = FixedDice(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4)
        with mock.patch.object(fire_calculations, "roll_1d6", dice):
            shot = FireCalculations(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)  # cluster spread, no single location
        self.assertEqual(shot.cluster_roll, 9)
        self.assertEqual(shot.cluster_hits_landed, 16)
        self.assertEqual(shot.damage, 16)  # total across the spread
        self.assertEqual([h.damage for h in shot.cluster_hits], [5, 5, 5, 1])
        self.assertTrue(all(h.location == FRONT_REAR_LOCATION_TABLE[7] for h in shot.cluster_hits))

    def test_cluster_srm6_splits_damage_across_locations(self):
        # SRM 6 (cluster, cluster_damage 5). Forced dice: to-hit 6+6=12 (hit),
        # cluster roll 4+5=9 -> 5 missiles on the size-6 table. 5 shots each.
        # across four independently-rolled locations (3+4=7 -> Center Torso).
        weapon = _weapon(name="SRM6", full_name="SRM 6", cluster=True, num_shots=6, cluster_damage=2, damage=12)
        dice = FixedDice(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4)
        with mock.patch.object(fire_calculations, "roll_1d6", dice):
            shot = FireCalculations(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertIsNone(shot.hit_location)  # cluster spread, no single location
        self.assertEqual(shot.cluster_roll, 9)
        self.assertEqual(shot.cluster_hits_landed, 5)
        self.assertEqual(shot.damage, 10)  # total across the spread
        self.assertEqual([h.damage for h in shot.cluster_hits], [2, 2, 2, 2, 2])

    def test_cluster_shot_serializes_to_json(self):
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20, cluster_damage=5, damage=20)
        dice = FixedDice(6, 6, 4, 5, 3, 4, 3, 4, 3, 4, 3, 4)
        with mock.patch.object(fire_calculations, "roll_1d6", dice):
            shot = FireCalculations(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        d = serialize_shot(shot)
        self.assertEqual(d["cluster_hits_landed"], 16)
        self.assertEqual([h["damage"] for h in d["cluster_hits"]], [5, 5, 5, 1])
        json.dumps(d)  # must not raise

    # -- critical hits ---------------------------------------------------

    def test_critical_hit_rerolls_location_and_flags(self):
        # A natural 2 on the hit-location roll is a through-armor crit: flag it
        # and reroll the location. Dice: to-hit 6+6=12 (hit), location 1+1=2
        # (crit), reroll 3+4=7 -> Center Torso.
        weapon = _weapon(name="ML", damage=5)
        with mock.patch.object(fire_calculations, "roll_1d6", FixedDice(6, 6, 1, 1, 3, 4)):
            shot = FireCalculations(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertTrue(shot.critical_hit)
        self.assertEqual((shot.all_rolls.location_1, shot.all_rolls.location_2), (1, 1))
        self.assertEqual((shot.all_rolls.tac_reroll_1, shot.all_rolls.tac_reroll_2), (3, 4))
        self.assertEqual(shot.hit_location, FRONT_REAR_LOCATION_TABLE[7])
        self.assertTrue(serialize_shot(shot)["critical_hit"])  # boolean reaches the UI

    def test_non_critical_hit_has_no_reroll(self):
        weapon = _weapon(name="ML", damage=5)
        with mock.patch.object(fire_calculations, "roll_1d6", FixedDice(6, 6, 3, 4)):
            shot = FireCalculations(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.SHORT,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertFalse(shot.critical_hit)
        self.assertIsNone(shot.all_rolls.tac_reroll_1)
        self.assertIsNone(shot.all_rolls.tac_reroll_2)
        self.assertFalse(serialize_shot(shot)["critical_hit"])

    def test_cluster_critical_hit_flags_individual_clusters(self):
        # LRM20: to-hit 6+6=12 (hit), cluster roll 1+1=2 -> 6 hits on size-20
        # table. damage_per_missile 1, missiles_per_group 5 -> groups [5, 1].
        # First cluster location 1+1=2 (crit) -> reroll 3+4=7; second 3+4=7 (no crit).
        weapon = _weapon(name="LRM20", cluster=True, num_shots=20, cluster_damage=5, damage=20)
        dice = FixedDice(6, 6, 1, 1, 1, 1, 3, 4, 3, 4)
        with mock.patch.object(fire_calculations, "roll_1d6", dice):
            shot = FireCalculations(
                weapon=weapon, target_number=7,
                target_facing="Front/Rear", range_band=RangeBand.LONG,
            ).resolve()
        self.assertTrue(shot.hit)
        self.assertEqual(shot.cluster_roll, 2)
        self.assertEqual(shot.cluster_hits_landed, 6)
        self.assertEqual([h.damage for h in shot.cluster_hits], [5, 1])
        self.assertEqual([h.critical_hit for h in shot.cluster_hits], [True, False])
        self.assertEqual(shot.cluster_hits[0].location, FRONT_REAR_LOCATION_TABLE[7])
        self.assertTrue(serialize_shot(shot)["cluster_hits"][0]["critical_hit"])


class ResolveFireTest(unittest.TestCase):
    # -- database lookup -------------------------------------------------

    def test_looks_weapon_up_by_name_and_uses_db_stats(self):
        resolver = _resolver(_weapon(name="AC20", full_name="AC/20", damage=20, heat=7))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["AC20"], pilot_gunnery_skill=4)
        shot = result["shots"][0]
        self.assertEqual(shot["weapon"], "AC/20")  # display name from the DB record
        self.assertEqual(shot["damage"], 20)
        self.assertEqual(result["total_heat"], 7)

    def test_unknown_weapon_name_is_reported_not_dropped_silently(self):
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
        self.assertEqual(result["misses"], 0)
        self.assertEqual(result["total_damage"], 20)

    def test_guaranteed_miss_deals_no_damage_but_accrues_heat(self):
        resolver = _resolver(_weapon(name="ML", damage=20, heat=7))
        with _all_ones():
            result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4)
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["total_damage"], 0)
        self.assertEqual(result["total_heat"], 7)  # heat accrues even on a miss
        self.assertEqual(result["shots"][0]["hit_location"], "Miss")

    # -- shot count (name repeated per shot) ----------------------------

    def test_repeated_name_fires_once_per_entry(self):
        resolver = _resolver(_weapon(name="ML", damage=1))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["ML", "ML", "ML", "ML"], pilot_gunnery_skill=4)
        self.assertEqual(len(result["shots"]), 4)
        self.assertEqual(result["total_damage"], 4)

    # -- target-number composition --------------------------------------

    def test_target_number_is_gunnery_plus_range_bracket(self):
        resolver = _resolver(_weapon(name="ML", short_range=3, medium_range=6, long_range=9))
        # distance 5 is in the medium bracket (short 3 < 5 <= medium 6) -> +2
        result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4, distance_modifier=5)
        self.assertEqual(result["shots"][0]["target_number"], 4 + 2)
        self.assertEqual(result["shots"][0]["range_band"], "MEDIUM")

    def test_modifiers_stack_into_target_number(self):
        resolver = _resolver(_weapon(name="ML"))
        # GATOR: gunnery 3 + attacker move 1 + target move 2 + additional 1 + short bracket 0
        result = resolver.resolve_fire(
            _unit(), ["ML"], pilot_gunnery_skill=3, distance_modifier=2,
            target_movement_modifier=2, self_movement_modifier=1, additional_modifier=1,
        )
        self.assertEqual(result["shots"][0]["target_number"], 3 + 1 + 2 + 1)
        self.assertEqual(result["shots"][0]["range_band"], "SHORT")

    def test_target_number_does_not_compound_across_shots(self):
        resolver = _resolver(_weapon(name="ML", short_range=3, medium_range=6, long_range=9))
        with _all_sixes():
            result = resolver.resolve_fire(
                _unit(), ["ML", "ML"], pilot_gunnery_skill=4, distance_modifier=8  # long
            )
        tns = {s["target_number"] for s in result["shots"]}
        self.assertEqual(tns, {4 + 4})

    # -- out of range ----------------------------------------------------

    def test_beyond_long_range_is_out_of_range(self):
        resolver = _resolver(_weapon(name="ML", long_range=9))
        result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4, distance_modifier=15)
        shot = result["shots"][0]
        self.assertIsNone(shot["target_number"])
        self.assertFalse(shot["hit"])
        self.assertEqual(shot["damage"], 0)
        self.assertEqual(shot["hit_location"], "Target Out of Range")
        self.assertIsNone(shot["range_band"])
        self.assertEqual(result["hits"], 0)

    # -- variable damage -------------------------------------------------

    def test_variable_damage_uses_band_specific_value(self):
        weapon = _weapon(
            name="Ultra", damage=0, variable_damage=True,
            short_range_damage=10, medium_range_damage=7, long_range_damage=4,
        )
        with _all_sixes():  # guaranteed hit so damage is applied
            result = _resolver(weapon).resolve_fire(
                _unit(), ["Ultra"], pilot_gunnery_skill=4, distance_modifier=8  # long bracket
            )
        self.assertEqual(result["shots"][0]["damage"], 4)

    def test_variable_damage_falls_back_to_flat_when_band_null(self):
        weapon = _weapon(name="Ultra", damage=6, variable_damage=True, short_range_damage=None)
        with _all_sixes():
            result = _resolver(weapon).resolve_fire(
                _unit(), ["Ultra"], pilot_gunnery_skill=4, distance_modifier=1  # short bracket
            )
        self.assertEqual(result["shots"][0]["damage"], 6)

    # -- return shape ----------------------------------------------------

    def test_result_contains_expected_keys(self):
        resolver = _resolver(_weapon(name="ML"))
        result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4, target_name="Locust")
        for key in (
                "attacker", "target", "target_movement_modifier", "shots",
                "hits", "misses", "total_damage", "total_heat", "unresolved_weapons",
        ):
            self.assertIn(key, result)
        self.assertEqual(result["attacker"], "Atlas")
        self.assertEqual(result["target"], "Locust")

    def test_result_is_json_serializable(self):
        resolver = _resolver(_weapon(name="ML", full_name="Medium Laser"))
        with _all_sixes():
            result = resolver.resolve_fire(_unit(), ["ML"], pilot_gunnery_skill=4, distance_modifier=2)
        json.dumps(result)  # must not raise: shots flatten weapon/range_band
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


class DoubleTapTest(unittest.TestCase):
    """The per-weapon double-tap flag must thread through to the Ultra-AC rules.

    ``resolve_ultra_ac`` is mocked so these assert the plumbing (which weapon
    double-taps) rather than the (still-placeholder) Ultra-AC damage math.
    """

    def _ultra(self, name="UAC5"):
        # A non-cluster ballistic tagged ULTRA — resolves via the standard path.
        return _weapon(name=name, cluster=False, num_shots=2,
                       modifications={"weapon_type": "ULTRA"})

    def _capture(self):
        return mock.patch.object(fire_calculations.UltraAcCalculations, "resolve_ultra_ac")

    def test_double_tap_flag_reaches_ultra_ac_calculator(self):
        with _all_sixes(), self._capture() as ultra:  # sixes -> guaranteed hit
            _resolver(self._ultra()).resolve_fire(
                _unit(), ["UAC5"], pilot_gunnery_skill=4, double_tap_flags=[True],
            )
        ultra.assert_called_once()
        self.assertIs(ultra.call_args.args[4], True)  # double_tap passed positionally

    def test_single_fire_ultra_passes_double_tap_false(self):
        with _all_sixes(), self._capture() as ultra:
            _resolver(self._ultra()).resolve_fire(
                _unit(), ["UAC5"], pilot_gunnery_skill=4, double_tap_flags=[False],
            )
        ultra.assert_called_once()
        self.assertIs(ultra.call_args.args[4], False)

    def test_missing_flags_default_to_no_double_tap(self):
        with _all_sixes(), self._capture() as ultra:
            _resolver(self._ultra()).resolve_fire(
                _unit(), ["UAC5"], pilot_gunnery_skill=4,  # no double_tap_flags
            )
        ultra.assert_called_once()
        self.assertIs(ultra.call_args.args[4], False)

    def test_non_ultra_weapon_never_calls_ultra_ac(self):
        with _all_sixes(), self._capture() as ultra:
            _resolver(_weapon(name="AC5")).resolve_fire(
                _unit(), ["AC5"], pilot_gunnery_skill=4, double_tap_flags=[True],
            )
        ultra.assert_not_called()

    def test_two_identical_ultras_double_tap_independently(self):
        # The instance-losing name collapse ("UAC5", "UAC5") must not lose the
        # per-weapon flags: index 0 double-taps, index 1 does not.
        with _all_sixes(), self._capture() as ultra:
            result = _resolver(self._ultra()).resolve_fire(
                _unit(), ["UAC5", "UAC5"], pilot_gunnery_skill=4,
                double_tap_flags=[True, False],
            )
        self.assertEqual(len(result["shots"]), 2)
        self.assertEqual(ultra.call_count, 2)
        self.assertEqual([c.args[4] for c in ultra.call_args_list], [True, False])

    def test_two_identical_ultras_both_double_tap(self):
        with _all_sixes(), self._capture() as ultra:
            _resolver(self._ultra()).resolve_fire(
                _unit(), ["UAC5", "UAC5"], pilot_gunnery_skill=4,
                double_tap_flags=[True, True],
            )
        self.assertEqual(ultra.call_count, 2)
        self.assertEqual([c.args[4] for c in ultra.call_args_list], [True, True])


if __name__ == "__main__":
    unittest.main()
