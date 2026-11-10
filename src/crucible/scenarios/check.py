"""crucible_check: the one scenario for checking Crucible in game. It grows as we go: each section sets up one thing
on its own strip of the map and adds a paragraph to the briefing.

Played with the Crucible data mod picked as the Data Mod.
"""

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import options_set, player_set

from crucible.bonuses import catalogue
from crucible.bonuses.model import Modifier
from crucible.datamod.shop import CHOICE_BUTTONS, choice_key
from crucible.datamod.upgrades import WONDER

NAME = "crucible_check"
SIZE = 60
REVEAL_MAP = 203

# Boons on the Wonder from the start (id -> button).
PLACED = {"carthaginians_4": 1}

# A boon that starts unplaced and is moved onto the Wonder by a trigger: (id, button, seconds).
MOVED = ("carthaginians_3", 2, 15)

RENAME_EVERY = 3  # seconds between the choices' live renames

BRIEFING = """Crucible check. Pick "Crucible" as the Data Mod. The map is revealed; nothing ends the game.

{sections}"""


def upgrades() -> list[Modifier]:
    """Every boon the check's data mod needs."""
    return [catalogue.by_id(upgrade_id) for upgrade_id in (*PLACED, MOVED[0])]


def _add(s, unit: str, x: float, y: float, player: int = 1) -> int:
    return s.unit_manager.add_unit(
        player=player,
        unit_const=tables.object_id(unit.upper(), "ror"),
        x=x + 0.5,
        y=y + 0.5,
    ).reference_id


def _units_for(s, modifier: Modifier, y: float) -> None:
    """A row of three of each unit `modifier` affects."""
    for k, target in enumerate(modifier.targets):
        for n in range(3):
            _add(s, target, 14 + k * 4 + n, y)


def _placed(s) -> str:
    """The Wonder, with the placed boons on its buttons and rows of the units they affect."""
    _add(s, "wonder", 6, 8)
    rows = []

    for row, (upgrade_id, button) in enumerate(PLACED.items()):
        modifier = catalogue.by_id(upgrade_id)
        _units_for(s, modifier, 4 + row * 4)
        rows.append(f"  button {button}: {modifier.name} ({modifier.rarity}): {modifier.description}")

    return (
        "BOONS on the Wonder (top left), priced by rarity and slow to research. Each row of units beside it is "
        "what a boon affects: check them, research it, check again. Do the buttons show these names, tooltips "
        "(with the cost) and icons?\n" + "\n".join(rows)
    )


def _moved(s, ctx, techs: dict[str, int]) -> str:
    """A boon that starts unplaced; a trigger moves it onto the Wonder (Change Technology Location)."""
    upgrade_id, button, seconds = MOVED
    modifier = catalogue.by_id(upgrade_id)
    _units_for(s, modifier, 4 + len(PLACED) * 4)

    ctx.trigger(
        "Move a boon onto the Wonder",
        [{"type": "timer", "timer": seconds}],
        [
            {
                "type": "change_technology_location",
                "source_player": 1,
                "technology": techs[upgrade_id],
                "object_list_unit_id_2": WONDER,
                "button_location": button,
            }
        ],
    )

    return (
        f"MOVING A BOON: {modifier.name} ({modifier.description}) isn't on any building at the start. At 0:{seconds} "
        f"a trigger should put it on the Wonder, button {button}. Does it appear there, and can you research it?"
    )


def _choices_xs(techs: dict[str, int]) -> str:
    """Renames the two choice buttons every RENAME_EVERY seconds with a counter, and reports in chat every state
    change of the choice techs (and each completed pick)."""
    choices = [(number, techs[choice_key(number)]) for number in range(1, len(CHOICE_BUTTONS) + 1)]
    labels = {1: "Stable", 2: "Economy"}
    decls = "".join(f"int crucibleChoiceState{n} = -9;\n" for n, _ in choices)

    renames = "".join(
        f'    xsSetTechName({tech}, 1, "{labels[n]} boons (" + crucibleLeft + " left)");\n'
        f'    xsSetTechDescription({tech}, 1, "Choose {labels[n]} boons. Renamed " + crucibleRenames + " times.");\n'
        for n, tech in choices
    )

    watches = "".join(
        f"""    state = xsGetTechState({tech}, 1);

    if (state != crucibleChoiceState{n}) {{
        xsChatData("Choice {n} state: %d", state);

        if (crucibleChoiceState{n} == cTechStateResearching) {{
            xsChatData("Choice {n} picked ({labels[n]})", 0);
        }}

        crucibleChoiceState{n} = state;
    }}

"""
        for n, tech in choices
    )

    return f"""// ---- crucible check: boon category choices ----
{decls}int crucibleLeft = 13;
int crucibleRenames = 0;

rule crucibleRenameChoices
    active
    minInterval {RENAME_EVERY}
{{
    crucibleRenames = crucibleRenames + 1;

    if (crucibleLeft > 0) {{
        crucibleLeft = crucibleLeft - 1;
    }}

{renames}}}

rule crucibleWatchChoices
    active
    highFrequency
{{
    int state = 0;

{watches}}}
"""


def _choices(ctx, techs: dict[str, int]) -> str:
    ctx.xs(_choices_xs(techs))

    return (
        f"CATEGORY CHOICES on the Wonder, row 3, buttons {CHOICE_BUTTONS[0]} and {CHOICE_BUTTONS[1]}. A script "
        f"renames them every {RENAME_EVERY} s with a counting-down number ('Stable boons (12 left)'): do the names "
        "and tooltips change live? Click one (free, 1 s): chat should say which you picked. Click it again: does it "
        "work twice? Chat also shows each state change."
    )


def build(out: Path, techs: dict[str, int]) -> Path:
    """`techs` is the data mod's manifest (what each boon and choice is as a tech)."""
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario

    try:
        with games.use("ror"):
            s.player_manager.active_players = 1
            player_set(
                o.handle,
                1,
                {
                    "civilization": "GREEK",
                    "starting_age": "DARK",  # Stone Age: later starts research techs (Nobility: cavalry +15% HP)
                    "human": True,
                    "population_cap": 200,
                    "food": 5000,
                    "wood": 5000,
                    "stone": 5000,
                    "gold": 5000,
                },
            )

            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)

            _add(s, "town_center", SIZE - 8, SIZE - 8)
            sections = [_placed(s), _moved(s, ctx, techs), _choices(ctx, techs)]
            ctx.flush_xs()

            ctx.trigger(
                "Reveal map",
                [],
                [
                    {
                        "type": "modify_resource",
                        "tribute_list": REVEAL_MAP,
                        "source_player": 1,
                        "quantity": 2,
                        "operation": "SET",
                    }
                ],
            )

            s.message_manager.instructions = BRIEFING.format(sections="\n\n".join(sections))
            player_set(o.handle, 1, {"initial_player_view_x": 14, "initial_player_view_y": 10})

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
