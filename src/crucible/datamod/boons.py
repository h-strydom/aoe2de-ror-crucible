"""The boons (crucible.boons) as hidden techs: one per boon per level, unplaced (the shop puts the one it offers on a
Wonder slot). Every level costs its rarity's price (RARITY_COSTS). Levels that don't compile yet are left out."""

from crucible.boons import catalogue
from crucible.boons.compile import commands
from crucible.boons.model import RARITY_COSTS, Boon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import NOWHERE, DataMod
from crucible.datamod.upgrades import RESEARCH_TIME


def key(boon: Boon, level: int) -> str:
    """The manifest key of a boon's level."""
    return f"boon {boon.id} {level}"


def title(boon: Boon, level: int) -> str:
    """"Swordsman line: HP (2/5)"; a boon bought once has no count."""
    return boon.title if boon.levels == 1 else f"{boon.title} ({level}/{boon.levels})"


def describe(boon: Boon, level: int) -> str:
    """"Choson 2, rare: Swordsman line: HP +8"."""
    return f"{boon.name}, {boon.rarity}: {boon.title} {boon.text(level)}"


def add(mod: DataMod) -> dict[str, str]:
    """Returns what was left out: manifest key -> why."""
    skipped = {}

    for boon in catalogue.ALL:
        for level in boon.steps:
            try:
                found = commands(boon, level, mod.data)
            except NotImplementedError as error:
                skipped[key(boon, level)] = str(error)
                continue

            name = f"Crucible {key(boon, level)}"
            text = describe(boon, level)
            mod.manifest[key(boon, level)] = mod.new_tech(
                name,
                effect=mod.new_effect(name, found),
                title=title(boon, level),
                description=text,
                tooltip=f"Research <b>{title(boon, level)}<b> (<cost>)\n{text}",
                icon=icon_id(boon.icon, mod.data),
                location=NOWHERE,
                button=0,
                research_time=RESEARCH_TIME,
                costs=RARITY_COSTS[boon.rarity].items(),
            )

    return skipped
