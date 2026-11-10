"""The Wonder as the shop: its buttons, and the techs that aren't boons.

The Wonder's 15 buttons are three rows of five:
  row 1 (1-5): boons on offer (they stack);
  row 3, columns 1-2 (11, 12): the two boon categories to choose between after a wave;
  row 3, column 5 (15): "Send next wave" (later).

A choice is a free, near-instant, repeatable tech: a script renames it to the category it stands for, and sees
when it's researched.
"""

from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod
from crucible.datamod.upgrades import WONDER

BOON_BUTTONS = (1, 2, 3, 4, 5)
CHOICE_BUTTONS = (11, 12)
NEXT_WAVE_BUTTON = 15
CHOICE_TIME = 1


def choice_key(number: int) -> str:
    """The manifest key of a choice tech: "choice_1", "choice_2"."""
    return f"choice_{number}"


def add(mod: DataMod) -> None:
    """The two category choices, on row 3; the script gives them their names."""
    for number, button in enumerate(CHOICE_BUTTONS, start=1):
        effect = mod.new_effect(f"Crucible {choice_key(number)}", [])

        mod.manifest[choice_key(number)] = mod.new_tech(
            f"Crucible {choice_key(number)}",
            effect=effect,
            title=f"Boon category {number}",
            tooltip=f"Research <b>Boon category {number}<b> (<cost>)\nChoose this category of boons.",
            icon=icon_id(Icon.TECHNOLOGY, mod.data),
            location=WONDER,
            button=button,
            research_time=CHOICE_TIME,
            repeatable=True,
        )
