"""The Wonder as the shop: its buttons, and the techs that aren't boons.

The Wonder's 15 buttons are three rows of five:
  row 1 (1-5): boons on offer (they stack);
  row 3, columns 1-2 (11, 12): the two boon categories to choose between after a wave;
  row 3, column 5 (15): "Send next wave" (later).

A choice is a free, near-instant tech that a script renames to the category it stands for. A researched tech never
comes back, so each wave uses a fresh pair: pair 1 sits on the Wonder from the start, later pairs start unplaced
and a trigger moves each onto the same buttons when its turn comes.
"""

from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import NOWHERE, DataMod
from crucible.datamod.upgrades import WONDER

BOON_BUTTONS = (1, 2, 3, 4, 5)
CHOICE_BUTTONS = (11, 12)
NEXT_WAVE_BUTTON = 15
TRAINER_BUTTON = 13  # the dummy-unit trainer (a test: train buttons don't disappear)
CHOICE_TIME = 1
TRAINER = "choice_trainer"


def choice_key(pair: int, number: int) -> str:
    """The manifest key of a choice tech: "choice_1_1" is pair 1's first choice."""
    return f"choice_{pair}_{number}"


def add(mod: DataMod, pairs: int = 1) -> None:
    """`pairs` pairs of category choices; the script gives them their names."""
    for pair in range(1, pairs + 1):
        for number, button in enumerate(CHOICE_BUTTONS, start=1):
            key = choice_key(pair, number)
            effect = mod.new_effect(f"Crucible {key}", [])

            mod.manifest[key] = mod.new_tech(
                f"Crucible {key}",
                effect=effect,
                title=f"Boon category {number}",
                tooltip=f"Research <b>Boon category {number}<b> (<cost>)\nChoose this category of boons.",
                icon=icon_id(Icon.TECHNOLOGY, mod.data),
                location=WONDER if pair == 1 else NOWHERE,
                button=button if pair == 1 else 0,
                research_time=CHOICE_TIME,
            )


def add_trainer(mod: DataMod) -> None:
    """A free dummy unit trained at the Wonder: a choice button that never disappears (a script removes each one
    trained)."""
    mod.manifest[TRAINER] = mod.new_unit(
        "Crucible choice trainer",
        template="scout",
        title="Choose (trainer)",
        location=WONDER,
        button=TRAINER_BUTTON,
        train_time=CHOICE_TIME,
    )
