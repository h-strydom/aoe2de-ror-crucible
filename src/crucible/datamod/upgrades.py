"""The catalogue's modifiers as hidden techs.

Handing out an upgrade is researching its tech: by trigger for the player or the enemy, at the start of a run for
metaprogression, or from a button (the Wonder's, for the shop).
"""

from crucible.bonuses.compile import commands
from crucible.bonuses.model import Modifier
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod

WONDER, RESEARCH_TIME = 276, 10


def tooltip(modifier: Modifier) -> str:
    return f"Research <b>{modifier.name}<b> (<cost>)\n{modifier.description}"


def add(mod: DataMod, modifiers: list[Modifier]) -> None:
    """One free tech per modifier, at the Wonder (buttons from 1); the manifest maps modifier id to tech id."""
    for index, modifier in enumerate(modifiers):
        effect = mod.new_effect(f"Crucible {modifier.id}", commands(modifier))

        mod.manifest[modifier.id] = mod.new_tech(
            f"Crucible {modifier.id}",
            effect=effect,
            title=modifier.name,
            tooltip=tooltip(modifier),
            icon=icon_id(modifier.icon, mod.data),
            location=WONDER,
            button=index + 1,
            research_time=RESEARCH_TIME,
        )
