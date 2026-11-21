"""The hub's techs: one per meta upgrade (meta.py), near instant (1 s), priced in the currency (food, wood, gold,
stone: placeholders, free for now); the hub's triggers decide what a research does. And the hub's own copy of each
place's building (meta.PLACES), aged to its tier's look, so each place shows only its own upgrades."""

from crucible import meta
from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod

RESEARCH_TIME = 1  # as quick as it gets: at 0 the game researches a tech by itself (it won the hub at once)
RESOURCE_IDS = (0, 1, 3, 2)  # meta.Upgrade.cost's food, wood, gold, stone as the data's resource ids


def aged(mod: DataMod, unit: int, age: int) -> int:
    """`unit` as its building looks in `age` (0 Stone to 3 Iron), by the age techs' upgrades."""
    from crucible.scenarios.run_meta import age_chains

    for first, chain in age_chains(mod.data).items():
        if unit == first or unit in chain.values():
            reached = [a for a in chain if a <= age]

            return chain[max(reached)] if reached else first

    return unit


def costs(upgrade: meta.Upgrade) -> list[tuple[int, int]]:
    return [(resource, amount) for resource, amount in zip(RESOURCE_IDS, upgrade.cost, strict=True) if amount]


def add(mod: DataMod) -> None:
    icon = icon_id(Icon.TECHNOLOGY, mod.data)

    for place in meta.PLACES:
        if place.copy:
            mod.manifest[place.copy_key] = mod.copy_unit(aged(mod, place.unit, meta.TIER_AGES[place.tier]))

    for upgrade in meta.UPGRADES:
        mod.manifest[upgrade.tech] = mod.new_tech(
            f"Crucible {upgrade.tech}",
            effect=mod.new_effect(f"Crucible {upgrade.tech}", []),
            title=upgrade.title,
            description=upgrade.description,
            tooltip=f"Research <b>{upgrade.title}<b> (<cost>)\n{upgrade.description}",
            icon=icon,
            location=meta.location(meta.place(upgrade.place), mod.manifest),
            button=upgrade.button,
            research_time=RESEARCH_TIME,
            costs=costs(upgrade),
        )
