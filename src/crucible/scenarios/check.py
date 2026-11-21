"""crucible_check: the one scenario for checking Crucible in game, built from a handful of named tests
(scenarios/checks/), picked with `crucible check --test <name>`.

Each test sets up its own strip of the map and adds a paragraph to the briefing. Standing rule: once a test is
confirmed in game, its module is deleted, so the scenario only holds what's still unconfirmed.

Played with the Crucible data mod picked as the Data Mod.
"""

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import options_set, player_set

from crucible.bonuses import catalogue
from crucible.bonuses.model import Modifier
from crucible.scenarios.checks import TESTS

NAME = "crucible_check"
SIZE = 60
STRIP = 12  # each test's strip of the map, from the top
REVEAL_MAP = 203

BRIEFING = """Crucible check: {names}. Pick "Crucible" as the Data Mod. The map is revealed; nothing ends the game.

{sections}"""


def add_unit(s, unit: str, x: float, y: float, player: int = 1) -> int:
    return s.unit_manager.add_unit(
        player=player,
        unit_const=tables.object_id(unit.upper(), "ror"),
        x=x + 0.5,
        y=y + 0.5,
    ).reference_id


def var_id(ctx, name: str) -> int:
    """A trigger variable's number, for xsSetTriggerVariable."""
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def boons(tests: list[str]) -> list[Modifier]:
    """Every boon the picked tests need in the data mod."""
    ids = dict.fromkeys(boon for name in tests for boon in TESTS[name].BOONS)

    return [catalogue.by_id(boon) for boon in ids]


def buttons(tests: list[str]) -> dict[str, int]:
    """Boons the picked tests want on the Wonder from the start (id -> button)."""
    return {boon: button for name in tests for boon, button in TESTS[name].BUTTONS.items()}


def datamods(tests: list[str]) -> tuple:
    """What the picked tests add to the data mod themselves (a test module's optional datamod(mod))."""
    return tuple(TESTS[name].datamod for name in tests if hasattr(TESTS[name], "datamod"))


def build(out: Path, techs: dict[str, int], tests: list[str]) -> Path:
    """`techs` is the data mod's manifest (what each boon and choice is as a tech)."""
    size = max(SIZE, *(getattr(TESTS[name], "SIZE", SIZE) for name in tests))  # a test may need a bigger map
    o = SESSIONS.new(size, game="ror")
    s = o.scenario

    try:
        with games.use("ror"):
            s.player_manager.active_players = max(getattr(TESTS[name], "PLAYERS", 1) for name in tests)
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

            for player in range(2, s.player_manager.active_players + 1):  # for tests that need more players
                player_set(
                    o.handle,
                    player,
                    {"civilization": "GREEK", "starting_age": "DARK", "human": False, "ai": "immobile"},
                )

            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)

            add_unit(s, "wonder", 6, 8)
            add_unit(s, "town_center", size - 8, size - 8)
            sections = [TESTS[name].setup(o, ctx, techs, top=4 + k * STRIP) for k, name in enumerate(tests)]
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

            s.message_manager.instructions = BRIEFING.format(names=", ".join(tests), sections="\n\n".join(sections))
            player_set(o.handle, 1, {"initial_player_view_x": 14, "initial_player_view_y": 10})

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
