"""Tiered boons to effect commands, through crucible.bonuses' compilers: each effect of a tier's step is compiled as
a modifier would be (its own stat and subject, or the boon's). A stat whose command sets a value rather than adding
to it (TOTALS) is compiled from the total up to that tier: the steps come in order, so the last one bought sets
what all of them make."""

from dataclasses import dataclass

from genieutils.datfile import DatFile

from crucible.bonuses.compile import Command
from crucible.bonuses.compile.stats import COMPILERS
from crucible.bonuses.model import Change, Group, Stat
from crucible.boons.model import Boon, Effect, Tier

TOTALS = (Stat.RESEARCH_TIME, Stat.RESEARCH_SPEED, Stat.CONVERSION_RESISTANCE)


@dataclass(frozen=True)
class Resolved:
    """An effect with the boon's stat and subject filled in: what the compilers read off a modifier."""

    id: str
    change: Change
    stat: Stat
    targets: tuple[str, ...]
    groups: tuple[Group, ...]
    techs: tuple[str, ...]


def resolve(boon: Boon, tier: Tier, n: int, effect: Effect) -> Resolved:
    own = effect.targets is None and effect.groups is None and effect.techs is None

    return Resolved(
        id=f"{boon.id} {tier.name.lower()} {n}",
        change=effect.change,
        stat=effect.stat or boon.stat,
        targets=boon.targets if own else effect.targets or (),
        groups=boon.groups if own else effect.groups or (),
        techs=boon.techs if own else effect.techs or (),
    )


def commands(boon: Boon, tier: Tier, data: DatFile) -> list[Command]:
    """Every effect of the tier; NotImplementedError if one doesn't compile yet."""
    found = []
    totals = {Boon._key(e): e for e in boon.total(tier)}

    for n, effect in enumerate(boon.steps[tier]):
        if (effect.stat or boon.stat) in TOTALS:
            effect = totals[Boon._key(effect)]

        resolved = resolve(boon, tier, n, effect)

        if resolved.stat not in COMPILERS:
            raise NotImplementedError(f"{resolved.id}: {resolved.stat} doesn't compile yet")

        found += COMPILERS[resolved.stat](resolved, data)

    return found
