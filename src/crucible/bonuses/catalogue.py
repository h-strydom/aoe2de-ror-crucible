"""Every modifier, and the queries the hand-outs need ("4 random stable upgrades").

Nothing is listed here by hand: the catalogue is whatever the civ modules define, so a new modifier shows up in
every query (and every shop or boon built from one) as soon as it's added.
"""

import random
from collections.abc import Iterable

from crucible.bonuses.civs import CIVS
from crucible.bonuses.model import Modifier, Stat

ALL: tuple[Modifier, ...] = tuple(m for civ in CIVS for m in civ.MODIFIERS)


def by_id(modifier_id: str) -> Modifier:
    return next(m for m in ALL if m.id == modifier_id)


def tags() -> set[str]:
    return {t for m in ALL for t in m.tags}


def query(
    tag: str | None = None,
    civ: str | None = None,
    stat: Stat | None = None,
    kind: str | None = None,
    pool: Iterable[Modifier] = ALL,
) -> list[Modifier]:
    """The modifiers matching every filter given."""
    return [
        m
        for m in pool
        if (tag is None or tag in m.tags)
        and (civ is None or m.civ == civ)
        and (stat is None or m.stat == stat)
        and (kind is None or m.kind == kind)
    ]


def pick(n: int, rng: random.Random, **filters) -> list[Modifier]:
    """Up to `n` different modifiers at random from the ones matching `filters` (see `query`)."""
    matches = query(**filters)
    return rng.sample(matches, min(n, len(matches)))
