"""crucible_check: the one scenario for checking Crucible in game. It grows as we go: each section sets up one thing
on its own strip of the map and adds a line to the briefing.

Played with the Crucible data mod picked as the Data Mod.
"""

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import options_set, player_set

from crucible.bonuses import catalogue
from crucible.bonuses.model import Modifier

NAME = "crucible_check"
SIZE = 60
REVEAL_MAP = 203

# What the check shows. Upgrades go on the Wonder in this order (buttons 1, 2, ...).
UPGRADES = ("carthaginians_4",)

BRIEFING = """Crucible check. Pick "Crucible" as the Data Mod. The map is revealed; nothing ends the game.

{sections}"""


def upgrades() -> list[Modifier]:
    return [catalogue.by_id(upgrade_id) for upgrade_id in UPGRADES]


def _add(s, unit: str, x: float, y: float, player: int = 1) -> int:
    return s.unit_manager.add_unit(
        player=player,
        unit_const=tables.object_id(unit.upper(), "ror"),
        x=x + 0.5,
        y=y + 0.5,
    ).reference_id


def _upgrades(s, modifiers: list[Modifier]) -> str:
    """The Wonder, with a row of three of each unit an upgrade affects."""
    _add(s, "wonder", 6, 8)
    rows = []

    for button, modifier in enumerate(modifiers, start=1):
        y = 4 + (button - 1) * 4

        for k, target in enumerate(modifier.targets):
            for n in range(3):
                _add(s, target, 14 + k * 4 + n, y)

        rows.append(f"  {button}. {modifier.name} ({modifier.rarity}): {modifier.description}")

    return (
        "UPGRADES on the Wonder (top left), priced by rarity and slow to research. Each row of units beside it is "
        "what an upgrade affects: check them, research it, check again. Do the buttons show these names, tooltips "
        "(with the cost) and icons?\n" + "\n".join(rows)
    )


def build(out: Path) -> Path:
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
                    "starting_age": "IMPERIAL",
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
            sections = [_upgrades(s, upgrades())]

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
