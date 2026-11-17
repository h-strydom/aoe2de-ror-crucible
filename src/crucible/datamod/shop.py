"""The Wonder as the shop: its buttons, and the techs that aren't boons.

The Wonder's 15 buttons are three rows of five:
  row 1 (1-5): boons on offer (they stack);
  row 3, columns 1-2 (11, 12): the two boon categories to choose between after a wave;
  row 2, column 1 (6): "End the run", once the waves are defeated;
  row 2, column 5 (10): "Send next wave", which a script turns on when a wave is in position.

A choice is a free, near-instant tech that a script renames to the category it stands for. One pair serves every
wave: a click disables the other choice (locked in), and when the pick finishes both are re-enabled (a researched
tech comes back that way) and renamed for the next wave.
"""

from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod
from crucible.datamod.upgrades import WONDER

BOON_BUTTONS = (1, 2, 3, 4, 5)
CHOICE_BUTTONS = (11, 12)
NEXT_WAVE_BUTTON = 10
CHOICE_TIME = 1
SEND_WAVE = "send_wave"  # its manifest key
END_RUN = "end_run"  # "End the run", once the waves are defeated
END_RUN_BUTTON = 6


def choice_key(number: int) -> str:
    """The manifest key of a choice tech: "choice_1", "choice_2"."""
    return f"choice_{number}"


def add(mod: DataMod) -> None:
    """The two category choices and the send button, on row 3; the script gives the choices their names."""
    for number, button in enumerate(CHOICE_BUTTONS, start=1):
        key = choice_key(number)
        effect = mod.new_effect(f"Crucible {key}", [])

        mod.manifest[key] = mod.new_tech(
            f"Crucible {key}",
            effect=effect,
            title=f"Boon category {number}",
            description="Choose this category of boons.",
            tooltip=f"Research <b>Boon category {number}<b> (<cost>)\nChoose this category of boons.",
            icon=icon_id(Icon.TECHNOLOGY, mod.data),
            location=WONDER,
            button=button,
            research_time=CHOICE_TIME,
        )

    mod.manifest[SEND_WAVE] = mod.new_tech(
        "Crucible send wave",
        effect=mod.new_effect("Crucible send wave", []),
        title="Send next wave",
        description="Send the waiting wave now. The next one walks in, and comes 5 minutes after this one.",
        tooltip="Research <b>Send next wave<b>\nSend the waiting wave now. The next one walks in, and comes 5 minutes "
        "after this one.",
        icon=icon_id(Icon.TECHNOLOGY, mod.data),
        location=WONDER,
        button=NEXT_WAVE_BUTTON,
        research_time=CHOICE_TIME,
    )
    mod.manifest[END_RUN] = mod.new_tech(
        "Crucible end run",
        effect=mod.new_effect("Crucible end run", []),
        title="End the run",
        description="You have defeated the waves: claim your victory and end the run.",
        tooltip="Research <b>End the run<b>\nYou have defeated the waves: claim your victory and end the run.",
        icon=icon_id(Icon.TECHNOLOGY, mod.data),
        location=WONDER,
        button=END_RUN_BUTTON,
        research_time=CHOICE_TIME,
    )
