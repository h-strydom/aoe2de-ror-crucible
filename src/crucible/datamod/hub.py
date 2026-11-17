"""The hub's techs: one per meta upgrade (meta.py), and "Begin the Crucible". Free and instant for now; the hub's
triggers decide what a research does."""

from crucible import meta
from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod

RESEARCH_TIME = 0  # instant


def add(mod: DataMod) -> None:
    icon = icon_id(Icon.TECHNOLOGY, mod.data)

    for upgrade in meta.UPGRADES:
        mod.manifest[upgrade.tech] = mod.new_tech(
            f"Crucible {upgrade.tech}",
            effect=mod.new_effect(f"Crucible {upgrade.tech}", []),
            title=upgrade.title,
            description=upgrade.description,
            tooltip=f"Research <b>{upgrade.title}<b> (<cost>)\n{upgrade.description}",
            icon=icon,
            location=upgrade.building,
            button=upgrade.button,
            research_time=RESEARCH_TIME,
        )

    mod.manifest[meta.BEGIN] = mod.new_tech(
        f"Crucible {meta.BEGIN}",
        effect=mod.new_effect(f"Crucible {meta.BEGIN}", []),
        title="Begin the Crucible",
        description="Leave the camp and start a run.",
        tooltip="Research <b>Begin the Crucible<b>\nLeave the camp and start a run.",
        icon=icon,
        location=meta.TOWN_CENTER,
        button=meta.BEGIN_BUTTON,
        research_time=RESEARCH_TIME,
    )
