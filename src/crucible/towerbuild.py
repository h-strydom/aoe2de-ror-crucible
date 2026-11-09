"""Can a villager build both a Ballista Tower and a Catapult Tower? (data mod)

A standalone scenario, `crucible_tower_build`, played with the Crucible Test Data mod picked. The data mod puts two
more towers in the villager's military build page: the Ballista Tower as a building of its own (slot 14; RoR only
reaches it by upgrading the other towers) and a new Catapult Tower (slot 15), a copy of the Guard Tower that fires a
Stone Thrower's stone with its attack (50 melee, +140 vs buildings), range 3-10 and splash for enemies only.

You start in the Iron Age with villagers and plenty of resources. Passive enemies and an enemy Barracks stand
nearby to shoot at.
"""
from __future__ import annotations

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_tower_build"
SIZE = 48
REVEAL_MAP = 203

INSTRUCTIONS = """Crucible tower build test. Pick "Crucible Test Data" as the Data Mod.

Select a villager and open the military build page: besides the Watch Tower there should be a Ballista Tower and a \
Catapult Tower. Build one of each near the enemies (to the right). Do both appear, build and fire? The Catapult \
Tower should lob stones, hit hard (50 melee, +140 vs buildings) and have a dead zone at its base (minimum range 3). \
Enemies don't fight back. Nothing ends the game."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def build(out: Path) -> Path:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": True,
                                     "food": 5000, "wood": 5000, "gold": 5000, "stone": 5000,
                                     "population_cap": 200})
            player_set(o.handle, 2, {"civilization": "PERSIAN", "starting_age": "IMPERIAL", "ai": "none"})
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            _add(s, 1, "TOWN_CENTER", 6, 20)
            for i in range(6):
                _add(s, 1, "VILLAGER_MALE", 12, 16 + i * 2)
            enemies = [_add(s, 2, "CLUBMAN", 30 + dx, 16 + dy) for dx in (0, 1, 2) for dy in (0, 2, 4, 6)]
            enemies += [_add(s, 2, "WAR_ELEPHANT", 34, 18 + k * 4) for k in range(2)]
            _add(s, 2, "BARRACKS", 36, 28)
            blocks.anchor(ctx, player=2, at=(46, 46))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": enemies,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}])
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 18, "initial_player_view_y": 20})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)
