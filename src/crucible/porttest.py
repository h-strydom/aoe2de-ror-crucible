"""Ported units and mutually exclusive techs (data mod).

A standalone scenario, `crucible_port_test`, played with the Crucible Test Data mod picked.

1. Units from AoE2's data file in Return of Rome: the Knight (its slot is RoR's Cavalry), the Crossbowman (ranged,
   so its projectiles come too) and the Chronicles Hoplite and Immortal. The data mod copies their data and every
   graphic, sound and linked unit they need (`port.py`); the sprites come from the player's own install. One of
   each stands ready, and the Barracks trains them.
2. Chronicles-style exclusive techs: each one's effect disables every tech in its set. Rounds 1-3 (type 9 techs,
   copied from RoR's Axe): two could be queued and both researched; a cost in a spare resource was ignored; a script
   disabling the others didn't hold. In Chronicles, hovering one draws a red cross over the other and the other
   can't be started while one researches. Round 4 compares the tech type: a type 0 set at the Barracks (Chronicles'
   unique techs) and a type 33 pair at the Town Center (the type of AoE2's Athenian governments and the Market's
   trade settings: switchable settings rather than a one-time pick). A read-only script reports each tech's state
   in chat whenever it changes.

Passive enemies (RoR units) stand to the right to fight.
"""
from __future__ import annotations

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import EXCLUSIVE, PORTED, exclusive_tech_ids, ported_ids

NAME = "crucible_port_test"
SIZE = 48
REVEAL_MAP = 203

INSTRUCTIONS = """Crucible ported units and exclusive techs test, round 5. Pick "Crucible Test Data" as the Data Mod.

UNITS: portraits, left to right, should be RoR's Heavy Cavalry, Improved Bowman, Hoplite and Centurion: are they?

EXCLUSIVE TECHS. Which buildings act like Chronicles (hover one: red cross over the others; while one researches \
the others can't be started; they vanish when it finishes)? \
1) BARRACKS: three new techs (Oligarchy, Democracy, Tyranny names), now the type Chronicles' unique techs use. \
2) TOWN CENTER: two new techs, the type AoE2 uses for switchable settings (Athenian governments). \
Chat reports each new tech's state when it changes: 1 ready, 4 queued, 2 researching, 3 done, -1 disabled. \
WONDER (new): select your Wonder (bottom left). Is there a tech button on it, named "Wonder"? Research it (free, \
10 s): you should get 500 of each resource. Nothing ends the game."""


def xs_code(techs: tuple[int, ...]) -> str:
    """Report each tech's state (`xsGetTechState`) in chat whenever it changes. Read-only."""
    names = [f"Barracks tech {k + 1}" for k in range(len(EXCLUSIVE))]
    names += [f"Town Center tech {k + 1}" for k in range(len(techs) - len(EXCLUSIVE))]
    decls = "".join(f"int crucibleTechState{k} = -9;\n" for k in range(len(techs)))
    body = "".join(f"""    if (xsGetTechState({t}, 1) != crucibleTechState{k}) {{
        crucibleTechState{k} = xsGetTechState({t}, 1);
        xsChatData("{name} state: %d", crucibleTechState{k});
    }}
""" for k, (t, name) in enumerate(zip(techs, names)))
    return f"""// ---- crucible exclusive techs: report state changes ----
{decls}
rule crucibleTechStates
    active
    highFrequency
{{
{body}}}
"""


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
            _add(s, 1, "WONDER", 8, 40)                    # round 5: a tech on the Wonder
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
            ctx.xs(xs_code(exclusive_tech_ids()))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 20, "initial_player_view_y": 22})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)
