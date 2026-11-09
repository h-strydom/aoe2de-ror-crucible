"""Ported units and mutually exclusive techs (data mod).

A standalone scenario, `crucible_port_test`, played with the Crucible Test Data mod picked.

1. Units from AoE2's data file in Return of Rome: the Knight (its slot is RoR's Cavalry), the Crossbowman (ranged,
   so its projectiles come too) and the Chronicles Hoplite and Immortal. The data mod copies their data and every
   graphic, sound and linked unit they need (`port.py`); the sprites come from the player's own install. One of
   each stands ready, and the Barracks trains them.
2. Three Chronicles-style exclusive techs at the Barracks: researching one disables all three. They pay 200 gold,
   wood or food so the pick shows. Two Barracks let you try starting two of them at once.

Passive enemies (RoR units) stand to the right to fight.
"""
from __future__ import annotations

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import PORTED, ported_ids

NAME = "crucible_port_test"
SIZE = 48
REVEAL_MAP = 203

INSTRUCTIONS = """Crucible ported units and exclusive techs test. Pick "Crucible Test Data" as the Data Mod.

UNITS: four units from AoE2 stand by your Barracks, left to right: Knight, Crossbowman (AoE2), Hoplite, Immortal \
(Chronicles). For each: does it look right standing, walking, attacking and dying (and leave a corpse)? Does the \
Crossbowman's bolt fly? Name, icon and sounds right? Fight the passive enemies on the right. The Barracks should \
also train all four (buttons on its page).

EXCLUSIVE TECHS: the Barracks has three new techs (named after Chronicles' Oligarchy, Democracy, Tyranny, if RoR \
has those strings). Each pays 200 (gold, wood, food). Research one: do the other two disappear? First, start two \
of them at the same time, one in each Barracks: what happens when the first finishes? Nothing ends the game."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def build(out: Path) -> Path:
    ids = ported_ids()
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": True,
                                     "food": 2000, "wood": 2000, "gold": 2000, "stone": 2000,
                                     "population_cap": 200})
            player_set(o.handle, 2, {"civilization": "PERSIAN", "starting_age": "IMPERIAL", "ai": "none"})
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            _add(s, 1, "TOWN_CENTER", 6, 20)
            for i in range(4):
                _add(s, 1, "VILLAGER_MALE", 12, 18 + i * 2)
            _add(s, 1, "BARRACKS", 16, 12)
            _add(s, 1, "BARRACKS", 16, 30)
            for k, uid in enumerate(PORTED):
                _add(s, 1, ids[uid], 20 + k * 2, 22)
            enemies = [_add(s, 2, "HOPLITE", 34 + dx, 16 + dy) for dx in (0, 2) for dy in (0, 3, 6, 9)]
            enemies += [_add(s, 2, "AXEMAN", 38, 18 + k * 3) for k in range(3)]
            blocks.anchor(ctx, player=2, at=(46, 46))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": enemies,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}])
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 20, "initial_player_view_y": 22})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)
