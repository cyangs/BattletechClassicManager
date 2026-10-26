"""Load and validate the hardcoded Aces AI control-card deck.

The deck lives in ``cards.json`` next to this module. It is loaded once on first
access and cached. Validation is intentionally light — the cards are authored by
hand and shipped with the app, so we only guard against the shape being wrong in
a way that would break the API/frontend contract.
"""

import json
from functools import lru_cache
from pathlib import Path

_DECK_PATH = Path(__file__).with_name("cards.json")

# Postures every card must define, in the order the UI presents them.
_REQUIRED_POSTURES = ("aggressive", "balanced", "cautious")


class AiDeckError(ValueError):
    """Raised when cards.json is missing required structure."""


def _validate(deck: dict) -> dict:
    """Light structural validation of the loaded deck. Returns it unchanged."""
    if not isinstance(deck, dict) or "cards" not in deck:
        raise AiDeckError("Deck must be an object with a 'cards' list.")
    if not isinstance(deck["cards"], list) or not deck["cards"]:
        raise AiDeckError("Deck 'cards' must be a non-empty list.")

    for i, card in enumerate(deck["cards"]):
        where = f"cards[{i}]"
        if not card.get("role"):
            raise AiDeckError(f"{where} is missing 'role'.")
        movement = card.get("movement") or {}
        postures = movement.get("postures") or {}
        for p in _REQUIRED_POSTURES:
            if p not in postures:
                raise AiDeckError(f"{where} ({card.get('role')}) is missing posture '{p}'.")
        if "combat" not in card:
            raise AiDeckError(f"{where} ({card.get('role')}) is missing 'combat'.")
    return deck


@lru_cache(maxsize=1)
def get_deck() -> dict:
    """The full deck object: ``{"version": int, "cards": [...]}``. Cached."""
    with _DECK_PATH.open(encoding="utf-8") as fh:
        deck = json.load(fh)
    return _validate(deck)


def get_cards() -> list:
    """All cards in the deck."""
    return get_deck()["cards"]


def cards_for_role(role: str) -> list:
    """Every card matching ``role`` (case-insensitive). Empty list if none."""
    if not role:
        return []
    want = role.strip().upper()
    return [c for c in get_cards() if str(c.get("role", "")).upper() == want]


def all_roles() -> list:
    """Sorted, de-duplicated list of roles present in the deck."""
    return sorted({str(c.get("role", "")).upper() for c in get_cards() if c.get("role")})
