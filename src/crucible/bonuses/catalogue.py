"""Every modifier, and the queries the hand-outs need ("4 random stable upgrades").

Nothing is listed here by hand: the catalogue is whatever the civ modules define, so a new modifier shows up in
every query (and every shop or boon built from one) as soon as it's added.
"""

import random
from collections.abc import Iterable

from crucible.bonuses.civs import CIVS
from crucible.bonuses.model import Category, Modifier, Tag

ALL: tuple[Modifier, ...] = tuple(m for civ in CIVS for m in civ.MODIFIERS)


def by_id(modifier_id: str) -> Modifier:
    return next(m for m in ALL if m.id == modifier_id)


def tags() -> set[Tag]:
    return {t for m in ALL for t in m.tags}


def query(*categories: Category, exclude: Iterable[Category] = (), pool: Iterable[Modifier] = ALL) -> list[Modifier]:
    """The modifiers in every one of `categories` and none of `exclude`, e.g.
    query(Tag.CAVALRY, exclude=[Tag.DRAWBACK])."""
    exclude = tuple(exclude)

    return [m for m in pool if all(m.in_category(c) for c in categories) and not any(m.in_category(c) for c in exclude)]


def pick(n: int, rng: random.Random, *categories: Category, exclude: Iterable[Category] = ()) -> list[Modifier]:
    """Up to `n` different modifiers at random from `query(*categories, exclude=exclude)`."""
    matches = query(*categories, exclude=exclude)

    return rng.sample(matches, min(n, len(matches)))
