"""Ported units and mutually exclusive techs (data mod).

A standalone scenario, `crucible_port_test`, played with the Crucible Test Data mod picked.

1. Units from AoE2's data file in Return of Rome: the Knight (its slot is RoR's Cavalry), the Crossbowman (ranged,
   so its projectiles come too) and the Chronicles Hoplite and Immortal. The data mod copies their data and every
   graphic, sound and linked unit they need (`port.py`); the sprites come from the player's own install. One of
   each stands ready, and the Barracks trains them.
2. Three Chronicles-style exclusive techs at the Barracks: researching one disables all three. They pay 200 gold,
   wood or food so the pick shows. Costs are paid at queue time, so the data alone let two be queued and both
   researched (round 1), and a cost in a spare resource is ignored (round 2): a script (`xs_code`) disables the
   others the moment one is queued. Two Barracks let you try two at once.

Passive enemies (RoR units) stand to the right to fight.
"""
from __future__ import annotations

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import EXCLUSIVE, EXCLUSIVE_COST, EXCLUSIVE_PAY, PORTED, exclusive_tech_ids, ported_ids

NAME = "crucible_port_test"
SIZE = 48
REVEAL_MAP = 203

INSTRUCTIONS = """Crucible ported units and exclusive techs test, round 3. Pick "Crucible Test Data" as the Data Mod.

UNITS (round 2: the Immortal switches to ranged and back). Portraits, left to right, should be RoR's Heavy \
Cavalry, Improved Bowman, Hoplite and Centurion: are they?

EXCLUSIVE TECHS (rounds 1-2: you could queue two and get both; a hidden token cost was ignored). Now a script \
watches the three Barracks techs: the moment one is queued, the other two should vanish from both Barracks, with a \
chat message. Cancel it: all three should come back. Try hard to queue two: click two quickly, or one in each \
Barracks at the same moment. If a second one still finishes, chat says it was refunded (50 food back, its 200 \
payout taken away). Nothing ends the game."""


def xs_code(techs: tuple[int, ...]) -> str:
    """Keep player 1's exclusive techs exclusive while queueing. The data mod's techs disable each other only when
    one finishes, and costs are paid at queue time, so two could be queued and both researched (round 1). This rule
    polls `xsGetTechState`: the moment one is queued or researching, the others are disabled; if it's cancelled
    (back to ready), they're enabled again. If a second one finishes anyway (queued in the same instant), its cost is
    refunded and its payout taken back."""
    def others(t: int, attr: str) -> str:
        return "".join(f"            xsEffectAmount(cModifyTech, {o}, {attr}, 0, 1);\n" for o in techs if o != t)

    pick = "".join(f"""        if ((crucibleChoice < 0) && ((xsGetTechState({t}, 1) == cTechStateQueued) ||
                (xsGetTechState({t}, 1) == cTechStateResearching) || (xsGetTechState({t}, 1) == cTechStateDone))) {{
            crucibleChoice = {t};
{others(t, "cAttributeDisable")}            xsChatData("Exclusive tech picked: %d (others disabled)", {k + 1});
        }}
""" for k, t in enumerate(techs))
    cancel = "".join(f"""        if (crucibleChoice == {t}) {{
{others(t, "cAttributeEnable")}        }}
""" for t in techs)
    done = "".join(f"""    if ((crucibleDone{k} == 0) && (xsGetTechState({t}, 1) == cTechStateDone)) {{
        crucibleDone{k} = 1;
        crucibleDoneCount = crucibleDoneCount + 1;
        if (crucibleDoneCount > 1) {{
            xsSetPlayerAttribute(1, 0, xsPlayerAttribute(1, 0) + {EXCLUSIVE_COST});
            xsSetPlayerAttribute(1, {res}, xsPlayerAttribute(1, {res}) - {EXCLUSIVE_PAY});
            xsChatData("A second exclusive tech finished (%d): refunded, payout taken back", {k + 1});
        }}
    }}
""" for k, (t, (_, res, _)) in enumerate(zip(techs, EXCLUSIVE)))
    flags = "".join(f"int crucibleDone{k} = 0;\n" for k in range(len(techs)))
    return f"""// ---- crucible exclusive techs: one at a time, even while queueing ----
int crucibleChoice = -1;
int crucibleDoneCount = 0;
{flags}
rule crucibleExclusive
    active
    highFrequency
{{
    if (crucibleChoice < 0) {{
{pick}    }} else if (xsGetTechState(crucibleChoice, 1) == cTechStateReady) {{
{cancel}        xsChatData("Exclusive tech cancelled: all three available again", 0);
        crucibleChoice = -1;
    }}
{done}}}
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
