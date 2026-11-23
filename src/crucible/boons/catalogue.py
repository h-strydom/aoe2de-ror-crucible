"""Every boon, and the offer roll.

An offer draws each choice from a different tag axis (a combat boon, a Stable boon, a team boon), then a boon at
random among those with that tag: no weighting yet (later, picking from a group more often will make it likelier).
"""

import random
from collections.abc import Iterable

from crucible.boons.civs import CIVS
from crucible.boons.model import MIN_CATEGORY, OFFER_AXES, Boon, Category, Flag

ALL: tuple[Boon, ...] = tuple(b for civ in CIVS for b in civ.BOONS)


def by_id(boon_id: str) -> Boon:
    return next(b for b in ALL if b.id == boon_id)


def query(*categories: Category, exclude: Iterable[Category] = (), pool: Iterable[Boon] = ALL) -> list[Boon]:
    exclude = tuple(exclude)

    return [b for b in pool if all(b.in_category(c) for c in categories) and not any(b.in_category(c) for c in exclude)]


def choices(pool: Iterable[Boon] = ALL) -> list[Category]:
    """The tags a choice can be: of the offer axes, with at least MIN_CATEGORY boons in `pool` (drawbacks never
    count)."""
    pool = [b for b in pool if not b.in_category(Flag.DRAWBACK)]

    return [c for axis in OFFER_AXES for c in axis if len(query(c, pool=pool)) >= MIN_CATEGORY]


def offer(n: int, rng: random.Random, pool: Iterable[Boon] = ALL) -> list[tuple[Category, Boon]]:
    """Up to `n` (category, boon) choices: each category from a different axis, each boon different, drawbacks never
    offered."""
    allowed = choices(pool)
    pool = [b for b in pool if not b.in_category(Flag.DRAWBACK)]
    axes = list(OFFER_AXES)
    rng.shuffle(axes)
    chosen: list[tuple[Category, Boon]] = []

    for axis in axes:
        if len(chosen) == n:
            break

        taken = {b.id for _, b in chosen}
        categories = [c for c in axis if c in allowed and any(b.id not in taken for b in query(c, pool=pool))]

        if not categories:
            continue

        category = rng.choice(categories)
        chosen.append((category, rng.choice([b for b in query(category, pool=pool) if b.id not in taken])))

    return chosen
