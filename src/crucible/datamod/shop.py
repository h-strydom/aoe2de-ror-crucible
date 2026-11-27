"""The Wonder as the shop: its buttons, and the techs that aren't boons.

The Wonder's 15 buttons are three rows of five:
  rows 1-2 (1-10): boons on offer, each on a free button; they stack only once all ten hold one;
  row 3, columns 1-2 (11, 12): the two boon categories to choose between after a wave;
  row 3, column 3 (13): Reroll, the boon categories on offer (the Trade Workshop's Rerolls): free while the run's
  free rerolls last, then the paid one (two techs, one shown at a time);
  row 3, column 4 (14): Spies, the whole map visible (the Trade Workshop's Spies);
  row 3, column 5 (15): "Send next wave", which a script turns on when a wave is in position.

A choice is a free, near-instant tech that a script renames to the category it stands for. One pair serves every
wave: a click disables the other choice (locked in), and when the pick finishes both are re-enabled (a researched
tech comes back that way) and renamed for the next wave.
"""

from crucible import meta
from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod
from crucible.datamod.upgrades import WONDER

BOON_BUTTONS = tuple(range(1, 11))
MAX_OFFERED = 5  # boons per choice at most (the More boons upgrade)
CHOICE_BUTTONS = (11, 12)
NEXT_WAVE_BUTTON = 15
CHOICE_TIME = 1
SEND_WAVE = "send_wave"  # its manifest key
REROLL_BUTTON, SPIES_BUTTON = 13, 14
REROLL_FREE, REROLL_PAID, SPIES = "reroll_free", "reroll_paid", "spies"  # manifest keys
GOLD = 3  # the data's resource id


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
        description="Send the waiting wave now. The next one walks in, and comes the usual time after this one.",
        tooltip="Research <b>Send next wave<b>\nSend the waiting wave now. The next one walks in, and comes the usual "
        "time after this one.",
        icon=icon_id(Icon.TECHNOLOGY, mod.data),
        location=WONDER,
        button=NEXT_WAVE_BUTTON,
        research_time=CHOICE_TIME,
    )
    reroll = "Show two other boon categories to choose between."

    for key, costs, title in (
        (REROLL_FREE, [], "Reroll (free)"),
        (REROLL_PAID, [(GOLD, meta.REROLL_GOLD)], "Reroll"),
    ):
        mod.manifest[key] = mod.new_tech(
            f"Crucible {key}",
            effect=mod.new_effect(f"Crucible {key}", []),
            title=title,
            description=reroll,
            tooltip=f"Research <b>{title}<b> (<cost>)\n{reroll}",
            icon=icon_id(Icon.TECHNOLOGY, mod.data),
            location=WONDER,
            button=REROLL_BUTTON,
            research_time=CHOICE_TIME,
            costs=costs,
        )

    spies = "Spies report on the whole map: everything is visible from now on."
    mod.manifest[SPIES] = mod.new_tech(
        "Crucible spies",
        effect=mod.new_effect("Crucible spies", []),
        title="Spies",
        description=spies,
        tooltip=f"Research <b>Spies<b> (<cost>)\n{spies}",
        icon=icon_id(Icon.TECHNOLOGY, mod.data),
        location=WONDER,
        button=SPIES_BUTTON,
        research_time=CHOICE_TIME,  # instant (playtest 2026-11-24)
        costs=[(GOLD, meta.SPIES_GOLD)],
    )
