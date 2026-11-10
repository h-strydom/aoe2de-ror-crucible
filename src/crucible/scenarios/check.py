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
from crucible.datamod.shop import CHOICE_BUTTONS, TRAINER, TRAINER_BUTTON, choice_key
from crucible.datamod.upgrades import WONDER

NAME = "crucible_check"
SIZE = 60
REVEAL_MAP = 203

# Boons on the Wonder from the start (id -> button).
PLACED = {"carthaginians_4": 1}

# A boon that starts unplaced and is moved onto the Wonder by a trigger: (id, button, seconds).
MOVED = ("carthaginians_3", 2, 15)

CHOICE_PAIRS = 2
CATEGORIES = {1: ("Stable", "Economy"), 2: ("Cavalry", "Greek")}  # the names each pair's two choices get
GONE = 162  # a Flag: "moving a tech away" puts it on a unit no player has
REMOVE, PLACE, REENABLE = "crucible_remove", "crucible_place", "crucible_reenable"  # trigger variables

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


def _var_id(ctx, name: str) -> int:
    """A trigger variable's number, for xsSetTriggerVariable."""
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def _choice_triggers(ctx, techs: dict[str, int]) -> None:
    """What the script asks for through trigger variables: remove a pair's other choice (pair 1 by disabling it,
    pair 2 by moving it to a Flag, to compare the two), place the next pair, and re-enable pair 1 at the end."""
    for name in (REMOVE, PLACE, REENABLE):
        ctx.var(name)

    for pair in range(1, CHOICE_PAIRS + 1):
        for number in (1, 2):
            tech = techs[choice_key(pair, number)]

            if pair == 1:
                removal = {"type": "enable_disable_technology", "source_player": 1, "technology": tech, "enabled": 0}
            else:
                removal = {
                    "type": "change_technology_location",
                    "source_player": 1,
                    "technology": tech,
                    "object_list_unit_id_2": GONE,
                    "button_location": 1,
                }

            ctx.trigger(
                f"Remove pair {pair} choice {number}",
                [{"type": "variable_value", "variable": REMOVE, "comparison": "EQUAL", "quantity": pair * 10 + number}],
                [removal],
            )

        if pair > 1:
            ctx.trigger(
                f"Place pair {pair}",
                [{"type": "variable_value", "variable": PLACE, "comparison": "EQUAL", "quantity": pair}],
                [
                    {
                        "type": "change_technology_location",
                        "source_player": 1,
                        "technology": techs[choice_key(pair, number)],
                        "object_list_unit_id_2": WONDER,
                        "button_location": button,
                    }
                    for number, button in enumerate(CHOICE_BUTTONS, start=1)
                ],
            )

    ctx.trigger(
        "Re-enable pair 1",
        [{"type": "variable_value", "variable": REENABLE, "comparison": "EQUAL", "quantity": 1}],
        [
            {
                "type": "enable_disable_technology",
                "source_player": 1,
                "technology": techs[choice_key(1, n)],
                "enabled": 1,
            }
            for n in (1, 2)
        ],
    )


def _choices_xs(techs: dict[str, int], variables: dict[str, int]) -> str:
    """Names every pair's choices, then runs the pairs: a click locks in (the other choice is removed at once);
    when the pick finishes, the next pair is placed; after the last, pair 1 is re-enabled (does a researched tech
    come back?). Also removes each dummy unit the trainer makes. Chat narrates."""
    names = "".join(
        f'    xsSetTechName({techs[choice_key(pair, n)]}, 1, "{CATEGORIES[pair][n - 1]} boons");\n'
        f'    xsSetTechDescription({techs[choice_key(pair, n)]}, 1, "Pair {pair}: {CATEGORIES[pair][n - 1]}.");\n'
        for pair in CATEGORIES
        for n in (1, 2)
    )
    tech_of = "".join(
        f"    if ((pair == {pair}) && (number == {n})) {{\n        return ({techs[choice_key(pair, n)]});\n    }}\n"
        for pair in range(1, CHOICE_PAIRS + 1)
        for n in (1, 2)
    )

    return f"""// ---- crucible check: boon category choices ----
int crucibleChoicePair = 1;
int crucibleChoicePicked = 0;
int crucibleTrained = 0;

int crucibleChoiceTech(int pair = 0, int number = 0) {{
{tech_of}    return (-1);
}}

rule crucibleNameChoices
    active
    highFrequency
{{
{names}    xsDisableSelf();
}}

rule crucibleRunChoices
    active
    highFrequency
{{
    int pair = crucibleChoicePair;

    if (pair > {CHOICE_PAIRS}) {{
        return;
    }}

    if (crucibleChoicePicked == 0) {{
        for (number = 1; < 3) {{
            int state = xsGetTechState(crucibleChoiceTech(pair, number), 1);

            if ((state == cTechStateResearching) || (state == cTechStateQueued)) {{
                crucibleChoicePicked = number;
                xsSetTriggerVariable({variables[REMOVE]}, pair * 10 + 3 - number);
                xsChatData("Pair %d: picked choice " + number + ", the other is removed", pair);
            }}
        }}

        return;
    }}

    if (xsGetTechState(crucibleChoiceTech(pair, crucibleChoicePicked), 1) == cTechStateDone) {{
        xsChatData("Pair %d: pick finished", pair);
        crucibleChoicePicked = 0;
        crucibleChoicePair = pair + 1;

        if (pair < {CHOICE_PAIRS}) {{
            xsSetTriggerVariable({variables[PLACE]}, pair + 1);
            xsChatData("Pair %d placed", pair + 1);
        }} else {{
            xsSetTriggerVariable({variables[REENABLE]}, 1);
            xsChatData("Re-enabling pair 1: does a button come back on 11 or 12?", 0);
        }}
    }}
}}

rule crucibleTrainerChoices
    active
    minInterval 1
{{
    int units = xsGetPlayerUnitIds(1, {techs[TRAINER]});

    for (i = 0; < xsArrayGetSize(units)) {{
        xsRemoveUnit(xsArrayGetInt(units, i));
        crucibleTrained = crucibleTrained + 1;
        xsChatData("Trainer used: %d", crucibleTrained);
    }}
}}
"""


def _choices(ctx, techs: dict[str, int]) -> str:
    _choice_triggers(ctx, techs)
    variables = {name: _var_id(ctx, name) for name in (REMOVE, PLACE, REENABLE)}
    ctx.xs(_choices_xs(techs, variables))
    first, second = CATEGORIES[1], CATEGORIES[2]

    return (
        f"CATEGORY CHOICES on the Wonder, row 3 (buttons {CHOICE_BUTTONS[0]} and {CHOICE_BUTTONS[1]}): "
        f"'{first[0]} boons' or '{first[1]} boons'. Click one: the other should vanish at once (you're locked in). "
        f"When it finishes (1 s), a new pair, '{second[0]}' or '{second[1]}', should appear in the same spots; same "
        "again. After that a trigger re-enables the first pair: does a button come back? Chat narrates each step.\n"
        f"TRAINER on button {TRAINER_BUTTON}: a free dummy unit. Train it a few times: chat should count each one "
        "and the unit should vanish. Does the button stay?"
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
