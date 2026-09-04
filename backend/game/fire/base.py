"""Base class for all weapon-shot resolvers.

:class:`BaseShotResolver` owns every piece of logic shared across fire modes:
dice rolling, through-armor critical (TAC) resolution, hit-location lookup,
range-band value selection, and the to-hit roll that guards the entry into a
hit.  Subclasses implement :meth:`_resolve_hit` to handle what happens once
the shot connects.
"""

import random
from abc import ABC, abstractmethod
from typing import Optional

from game.tables import (
    RIGHT_SIDE_LOCATION_TABLE,
    FRONT_REAR_LOCATION_TABLE,
    LEFT_SIDE_LOCATION_TABLE,
)
from game.fire.models import (
    RangeBand,
    DiceRollsResults,
    ClusterHit,
    WeaponShot,
)
from database.models.weapon import Weapon


# Which hit-location table a shot rolls on, keyed by the target's facing.
# Front/Rear is the default for any unrecognized facing.
_LOCATION_TABLE_BY_FACING = {
    "Left Side": LEFT_SIDE_LOCATION_TABLE,
    "Right Side": RIGHT_SIDE_LOCATION_TABLE,
    "Front/Rear": FRONT_REAR_LOCATION_TABLE,
}


# ---------------------------------------------------------------------------
# Dice helpers (module-level so they can be imported and used anywhere)
# ---------------------------------------------------------------------------

def roll_2d6() -> int:
    """The all-important 2d6 roller."""
    return random.randint(1, 6) + random.randint(1, 6)


def roll_1d6() -> int:
    """ The 1d6 roller."""
    return random.randint(1, 6)


# ---------------------------------------------------------------------------
# Base resolver
# ---------------------------------------------------------------------------

class BaseShotResolver(ABC):
    """Shared machinery for every fire resolution mode.

    Construct with the shot's context, then call :meth:`resolve` to get a
    fully populated :class:`~game.fire.models.WeaponShot`.
    """

    def __init__(
        self,
        weapon: Weapon,
        target_number: Optional[int],
        target_facing: str,
        range_band: Optional[RangeBand] = None,
        attachments: Optional[list] = None,
        targeting_computer_active: bool = False,
    ):
        self.weapon = weapon
        self.target_number = target_number
        self.target_facing = target_facing
        self.range_band = range_band
        self.critical_hit = False
        # Missile fire-control attachments in effect for this shot (e.g.
        # ["ARTEMISIV"]). Empty when none are fitted.
        self.attachments = attachments or []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def resolve(self) -> WeaponShot:
        """Roll out the shot and return the populated record."""
        # Out of range -> automatic miss. The roll/hit/damage fields keep their
        # defaults so callers inspecting the shot never see them unset.
        if self.target_number is None:
            return self._shot(hit_location="Target Out of Range")

        """ The all important to hit roll. Rolls a pair of 1D6 dice."""
        to_hit_1, to_hit_2 = roll_1d6(), roll_1d6()
        """ Sum of the pair of dice roll"""
        to_hit_roll = to_hit_1 + to_hit_2
        """ Store results for UI display"""
        all_rolls = DiceRollsResults(to_hit_1, to_hit_2)

        """ Applies any adjustments to the target number. Such as pulse weaponry"""
        target_number = self._adjusted_target_number()
        if to_hit_roll < target_number:
            return self._shot(
                target_number=target_number,
                roll=to_hit_roll,
                hit=False,
                hit_location="Miss",
                all_rolls=all_rolls,
            )

        """ Shot hit. Delegate to the subclass. """
        return self._resolve_hit(target_number, to_hit_roll, all_rolls)

    # ------------------------------------------------------------------
    # Abstract hook — subclasses implement their own hit resolution
    # ------------------------------------------------------------------

    @abstractmethod
    def _resolve_hit(
        self,
        target_number: int,
        to_hit_roll: int,
        all_rolls: DiceRollsResults,
    ) -> WeaponShot:
        """Resolve a confirmed hit and return the populated WeaponShot.

        Called by :meth:`resolve` after the to-hit roll succeeds.
        ``target_number`` is the *adjusted* value (pulse modifier applied).
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _shot(self, **overrides) -> WeaponShot:
        """Build a WeaponShot carrying this shot's context plus the outcome.

        ``overrides`` win over the context defaults (e.g. the adjusted
        ``target_number`` on a resolved shot).
        """
        fields = {
            "weapon": self.weapon,
            "target_number": self.target_number,
            "target_facing": self.target_facing,
            "range_band": self.range_band,
            "critical_hit": self.critical_hit,
        }
        fields.update(overrides)
        return WeaponShot(**fields)

    def _resolve_location_with_tac(self) -> tuple[int, bool, list[int]]:
        """Roll a hit location and apply through-armor critical (TAC) resolution.

        Returns a tuple of:
          - ``final_roll``  — the 2d6 sum to look up in the location table
          - ``critical_hit`` — True when the initial roll was a 2 (TAC triggered)
          - ``raw_dice``    — list of the individual d6 values rolled, in order:
              [loc_1, loc_2] for a normal hit, or
              [loc_1, loc_2, tac_1, tac_2] when a TAC reroll occurred.
        """
        loc_1, loc_2 = roll_1d6(), roll_1d6()
        roll = loc_1 + loc_2
        critical_hit = roll == 2
        if critical_hit:
            tac_1, tac_2 = roll_1d6(), roll_1d6()
            roll = tac_1 + tac_2
            return roll, critical_hit, [loc_1, loc_2, tac_1, tac_2]
        return roll, critical_hit, [loc_1, loc_2]

    def _hit_location(self, location_roll: int) -> str:
        table = _LOCATION_TABLE_BY_FACING.get(self.target_facing, FRONT_REAR_LOCATION_TABLE)
        return table.get(location_roll, "Unknown Location")

    def _band_value(self, short, medium, long):
        """Return the value that corresponds to this shot's range band.

        A convenience for the common pattern of mapping SHORT/MEDIUM/LONG to
        three weapon attributes. Returns ``None`` when ``range_band`` is unset.
        """
        return {
            RangeBand.SHORT: short,
            RangeBand.MEDIUM: medium,
            RangeBand.LONG: long,
        }.get(self.range_band)

    def _adjusted_target_number(self) -> int:
        """Apply the weapon's own per-band to-hit modifier, if any.

        A variable pulse laser, for example, stores -3/-2/-1 for
        short/medium/long. The (signed) modifier for this shot's band is added
        to the target number, so a negative value makes the shot easier to land.
        """
        modifier = self._weapon_range_modifier()
        if modifier is None:
            return self.target_number
        return self.target_number + modifier

    def _weapon_range_modifier(self) -> Optional[int]:
        """The weapon's stored to-hit modifier for this shot's range band."""
        return self._band_value(
            self.weapon.short_range_modifier,
            self.weapon.medium_range_modifier,
            self.weapon.long_range_modifier,
        )

    def _effective_damage(self) -> int:
        """Damage the weapon deals in this band (flat unless variable-damage)."""
        flat = int(self.weapon.damage or 0)
        if not self.weapon.variable_damage or self.range_band is None:
            return flat

        per_band = self._band_value(
            self.weapon.short_range_damage,
            self.weapon.medium_range_damage,
            self.weapon.long_range_damage,
        )
        # NULL per-band damage falls back to the flat damage value.
        return int(per_band) if per_band is not None else flat

    def _weapon_type(self) -> Optional[str]:
        """The weapon's sub-classification from its modifications blob (e.g. 'ULTRA').

        ``modifications`` is nullable, so guard against None.
        """
        return (getattr(self.weapon, "modifications", None) or {}).get("weapon_type")
