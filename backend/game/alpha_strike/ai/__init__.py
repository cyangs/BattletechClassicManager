"""Aces AI control cards.

A static, hardcoded deck of role-based "AI control cards" (loaded from
``cards.json``) that the GM uses to drive the automated side. These are plain
reference text — the app does not evaluate board positions or pick targets; it
just serves the deck so the frontend can pick a random card for a unit's role
and display its movement + combat instructions.

    from game.alpha_strike.ai import get_deck, cards_for_role, all_roles
"""

from game.alpha_strike.ai.loader import (
    get_deck,
    get_cards,
    cards_for_role,
    all_roles,
)

__all__ = [
    "get_deck",
    "get_cards",
    "cards_for_role",
    "all_roles",
]
