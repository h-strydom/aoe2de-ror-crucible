"""A one-screen scenario to check an upgrade in game: a Wonder with the upgrade's button, and units it affects.

Played with the Crucible data mod picked as the Data Mod.
"""

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import options_set, player_set

from crucible.bonuses.model import Modifier

NAME = "crucible_upgrade_check"
SIZE = 40
REVEAL_MAP = 203

INSTRUCTIONS = """Crucible upgrade check. Pick "Crucible" as the Data Mod.

Select your Wonder: its first button is the upgrade "{name}" ({description}). Check the units beside it, research \
the upgrade (free, 10 seconds), and check them again. Also: does the button show that name, that tooltip and an \
icon?"""


def _add(s, player: int, unit: str, x: float, y: float) -> int:
    return s.unit_manager.add_unit(
        player=player,
        unit_const=tables.object_id(unit.upper(), "ror"),
        x=x + 0.5,
        y=y + 0.5,
    ).reference_id


def build(modifier: Modifier, out: Path) -> Path:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 1
            player_set(
                o.handle,
                1,
                {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": True, "population_cap": 200},
            )
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            _add(s, 1, "wonder", 12, 20)
            _add(s, 1, "town_center", 30, 30)
            for k, target in enumerate(modifier.targets):
                for row in range(3):
                    _add(s, 1, target, 20 + k * 3, 16 + row * 3)
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
            s.message_manager.instructions = INSTRUCTIONS.format(
                name=modifier.name,
                description=modifier.description,
            )
            player_set(o.handle, 1, {"initial_player_view_x": 18, "initial_player_view_y": 20})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)
