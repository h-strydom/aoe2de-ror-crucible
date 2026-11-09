"""AoE2 mechanics in RoR, part 2: unit tasks and techs from the data mod.

A standalone scenario, `crucible_mech_data_test`, played with the Crucible Test Data mod picked. The data mod copies
AoE2 unit tasks onto RoR units and adds techs (testmod.py, `_mechanics`):

| Area | Test |
|---|---|
| Phalanx | RoR Hoplites get the Chronicles Hoplite's count aura: +2 armour per Hoplite within 3 tiles, up to +8. A
  cluster of five and a lone one; the ported Chronicles Hoplites (cluster and lone) for comparison |
| Building aura | The Town Center speeds up infantry within 10 tiles (x1.5) |
| Loot | Axemen carry the Camel Raider's loot task (gold from kills) |
| HP transform | Short Swordsmen turn into Long Swordsmen below 50% HP (the Jian Swordsman's task) |
| Extra spawn | A Clubman trained at the Barracks brings a second one (the Blackwood archer's task) |
| Mule Cart | AoE2's movable drop site, ported, with villagers by a far-off forest |
| Wonder | Techs: 500 of everything, spawn 3 War Elephants at the Town Center, curse (enemy infantry HP x0.5), team gift
  (+500 food for your team, including your ally) |

A script logs resources and unit counts every 5 seconds to `<profile>/profile/crucible_mech_data_test.xsdat`;
`crucible mech-data-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import CLUBMAN, LONG_SWORDSMAN, MULE_CART, SHORT_SWORDSMAN, WAR_ELEPHANT, ported_ids

NAME = "crucible_mech_data_test"
SIZE = 64
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322002, 1, 1, 5
REVEAL_MAP = 203
CHRONICLES_HOPLITE = 2110
COUNTED = (CLUBMAN, SHORT_SWORDSMAN, LONG_SWORDSMAN, WAR_ELEPHANT)

INSTRUCTIONS = """Crucible mechanics test, part 2. Pick "Crucible Test Data" as the Data Mod. The map is revealed; \
nothing ends the game.

PHALANX (top left): select a Hoplite in the cluster of five, then the lone one: is the cluster's armour higher (+2 \
per nearby Hoplite, up to +8)? Same for the ported Chronicles Hoplites below them.
TOWN CENTER AURA: infantry within 10 tiles of your Town Center should move 1.5x faster. Walk the Axemen beside the \
TC and the ones far right the same distance: are the near ones faster?
LOOT (top right): your Axemen attack passive Clubmen. Does your gold go up per kill?
HP TRANSFORM: enemy Axemen attack your two Short Swordsmen. Below 50% HP, do they become Long Swordsmen?
EXTRA SPAWN: train a Clubman at the Barracks (bottom right): do two come out?
MULE CART (bottom right corner): set the villagers chopping the forest. Do they drop wood at the Mule Cart? Can you \
move it? Its portrait may be wrong.
WONDER (bottom left), four techs: 500 of everything; 3 War Elephants at your Town Center; a curse halving enemy \
infantry HP (the Hoplites in the middle); +500 food for your team (check your ally in the scores too)."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(enemy_hoplite: int) -> str:
    """Every INTERVAL seconds: player 1's food, wood, gold, stone; player 3's food; player 1's counts of COUNTED;
    one enemy Hoplite's HP."""
    counts = "".join(f"    xsWriteInt(xsGetObjectCount(1, {u}));\n" for u in COUNTED)
    return f"""// ---- crucible mechanics test, part 2 ----
rule crucibleMechDataInit
    active
    highFrequency
{{
    xsCreateFile(false);
    xsWriteInt({MAGIC});
    xsWriteInt({VERSION});
    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleMechDataSample
    active
    minInterval {INTERVAL}
{{
    int hp = -1;
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
    for (r = 0; < 4) {{
        xsWriteInt(xsPlayerAttribute(1, r));
    }}
    xsWriteInt(xsPlayerAttribute(3, 0));
{counts}    if (xsDoesUnitExist({enemy_hoplite})) {{
        hp = xsGetUnitHitpoints({enemy_hoplite});
    }}
    xsWriteInt(hp);
    xsCloseFile();
}}
"""


def build(out: Path) -> Path:
    ids = ported_ids()
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 3
            for p in (1, 2, 3):
                fields = {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": p == 1,
                          "food": 2000 if p == 1 else 0, "wood": 2000 if p == 1 else 0,
                          "gold": 2000 if p == 1 else 0, "stone": 2000 if p == 1 else 0, "population_cap": 200}
                if p > 1:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            diplomacy_set(o.handle, 1, [3], "ALLY")
            diplomacy_set(o.handle, 2, [3], "NEUTRAL")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            passive, start = [], []

            # Phalanx: clusters of five and lone ones, RoR Hoplites and the ported Chronicles Hoplites.
            for row, unit in ((6, "HOPLITE"), (14, ids[CHRONICLES_HOPLITE])):
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0.5, 2)):
                    _add(s, 1, unit, 6 + dx, row + dy)
                _add(s, 1, unit, 20, row)

            # Town Center aura: Axemen beside the TC, and the same far away.
            _add(s, 1, "TOWN_CENTER", 6, 30)
            for k in range(3):
                _add(s, 1, "AXEMAN", 11, 28 + k * 2)
                _add(s, 1, "AXEMAN", 36, 28 + k * 2)

            # Loot: Axemen against passive Clubmen.
            looters = [_add(s, 1, "AXEMAN", 34, 4 + k * 2) for k in range(3)]
            victims = [_add(s, 2, "CLUBMAN", 38 + dx, 4 + dy) for dx in (0, 1.5) for dy in (0, 2, 4)]
            passive += victims
            start.append({"type": "task_object", "source_player": 1, "selected_object_ids": looters,
                          "location_object_reference": victims[0]})

            # HP transform: enemy Axemen attack two Short Swordsmen.
            swords = [_add(s, 1, "SHORT_SWORDSMAN", 34, 14 + k * 2) for k in range(2)]
            attackers = [_add(s, 2, "AXEMAN", 37, 13 + k * 2) for k in range(3)]
            for k, a in enumerate(attackers):
                start.append({"type": "task_object", "source_player": 2, "selected_object_ids": [a],
                              "location_object_reference": swords[k % 2]})

            # Curse target: passive enemy Hoplites in the middle.
            hoplites = [_add(s, 2, "HOPLITE", 28 + k * 1.5, 40) for k in range(3)]
            passive += hoplites

            # Extra spawn: a Barracks. Mule Cart: villagers by a forest far from the Town Center.
            _add(s, 1, "BARRACKS", 44, 44)
            for x in range(55, 62):
                for y in range(52, 62):
                    if (x + y) % 2 == 0:
                        _add(s, 0, "TREE_A", x, y)
            _add(s, 1, ids[MULE_CART], 51, 56)
            for k in range(4):
                _add(s, 1, "VILLAGER_MALE", 52, 53 + k * 2)

            # The Wonder, and the ally's base.
            _add(s, 1, "WONDER", 10, 52)
            _add(s, 3, "TOWN_CENTER", 58, 30)
            blocks.anchor(ctx, player=2, at=(62, 2))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": passive,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}])
            ctx.trigger("Start", [{"type": "timer", "timer": 3}], start)
            ctx.xs(xs_code(hoplites[0]))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 22, "initial_player_view_y": 22})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)


def report(record: Path) -> str:
    vals = list(struct.unpack_from(f"<{record.stat().st_size // 4}i", record.read_bytes()))
    if vals[0] != MAGIC:
        raise ValueError("not a crucible mechanics data test record")
    width = 2 + 4 + 1 + len(COUNTED) + 1
    i = 2
    lines = ["time   food/wood/gold/stone   ally food   clubmen short-sw long-sw elephants   enemy hoplite HP"]
    while i + width <= len(vals) and vals[i] == TAG_SAMPLE:
        t, f, w, g, st, ally, club, short, long_, eleph, hp = vals[i + 1:i + width]
        lines.append(f"{t // 60}:{t % 60:02}   {f}/{w}/{g}/{st}   {ally}   {club} {short} {long_} {eleph}   {hp}")
        i += width
    return "\n".join(lines)
