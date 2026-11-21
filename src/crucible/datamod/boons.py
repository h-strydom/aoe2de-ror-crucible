"""The tiered boons (crucible.boons) as hidden techs: one per boon per tier, unplaced and free for now (a trigger or
XS researches them). Tiers that don't compile yet are left out."""

from crucible.bonuses.model import Icon
from crucible.boons import catalogue
from crucible.boons.compile import commands
from crucible.boons.model import Boon, Tier
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import NOWHERE, DataMod


def key(boon: Boon, tier: Tier) -> str:
    """The manifest key of a boon's tier."""
    return f"boon {boon.id} {tier.name.lower()}"


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
            text = boon.text(tier)
            mod.manifest[key(boon, tier)] = mod.new_tech(
                name,
                effect=mod.new_effect(name, found),
                title=title,
                description=text,
                tooltip=f"Research <b>{title}<b>\n{text}",
                icon=icon_id(Icon.TECHNOLOGY, mod.data),
                location=NOWHERE,
                button=0,
                research_time=1,
            )

    return skipped
