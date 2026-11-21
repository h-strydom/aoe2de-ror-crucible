"""The tiered boons (crucible.boons) as hidden techs: one per boon per tier, unplaced (the shop puts the one it rolls
on a Wonder slot). Each tier costs its own price (TIER_COSTS): a roll up costs more. Tiers that don't compile yet are
left out."""

from crucible.boons import catalogue
from crucible.boons.compile import commands
from crucible.boons.model import TIER_COSTS, Boon, Tier
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import NOWHERE, DataMod
from crucible.datamod.upgrades import RESEARCH_TIME


def key(boon: Boon, tier: Tier) -> str:
    """The manifest key of a boon's tier."""
    return f"boon {boon.id} {tier.name.lower()}"


def describe(boon: Boon, tier: Tier) -> str:
    """"Choson 2 Heirloom: Swordsman line: HP +45 & +1 melee armour & +1 pierce armour"."""
    return f"{boon.name} {tier.title}: {boon.title} {boon.text(tier)}"


def add(mod: DataMod) -> dict[str, str]:
    """Returns what was left out: manifest key -> why."""
    skipped = {}

    for boon in catalogue.ALL:
        for tier in boon.tiers:
            try:
                found = commands(boon, tier, mod.data)
            except NotImplementedError as error:
                skipped[key(boon, tier)] = str(error)
                continue

            name = f"Crucible {key(boon, tier)}"
            title = f"{boon.title} ({tier.title})"
            text = describe(boon, tier)
            mod.manifest[key(boon, tier)] = mod.new_tech(
                name,
                effect=mod.new_effect(name, found),
                title=title,
                description=text,
                tooltip=f"Research <b>{title}<b> (<cost>)\n{text}",
                icon=icon_id(boon.icon, mod.data),
                location=NOWHERE,
                button=0,
                research_time=RESEARCH_TIME,
                costs=TIER_COSTS[tier].items(),
            )

    return skipped
