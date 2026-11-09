"""The resource test, round 2: resources that hold a different resource, and conversion by script.

A standalone scenario, `crucible_resource_test`, played from the Scenario lobby with the Crucible Test Data mod as
the Data Mod. Each idea gets its own allied computer player; every gatherer starts working on its own.

| Player | Test |
|---|---|
| 1 (you) | A fishing boat on a fish switched to hold **gold** (one object) |
| 2 | Lumberjacks on trees switched to hold **gold** (per tree) |
| 3 | Foragers on berry bushes switched to hold **stone** (per bush) |
| 4 | Lumberjacks on a tree type switched to **stone** for the whole type (does it reach trees already placed?) |
| 5 | Normal lumberjacks; a script pays **10% of their wood as gold** |
| 6 | Normal lumberjacks: the control |

Round 1 (work rate 0, gather multipliers, generation, trickles, chopping gold, boats told to take wood) is settled;
its results are in docs/feasibility.md.

A script writes every player's stockpile, and each tracked pile's remaining amount and stored resource type, every
10 seconds to `<profile>/profile/crucible_resource_test.xsdat`; `crucible resource-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

CAMPAIGN = "crucible_resource_test"
SIZE = 64
MAGIC, VERSION, TAG_SAMPLE = 412320777, 2, 1
INTERVAL = 10
STORAGE_TYPE = 168                     # object attribute: the resource a pile holds (first storage)
FOOD, WOOD, STONE, GOLD = 0, 1, 2, 3
WOOD_TOTAL = 167                       # player attribute: wood gathered so far
CONVERT_PLAYER, CONVERT_SHARE = 5, 0.1
REVEAL_MAP, SET = 203, 1
UNIT_ATTRIBUTE_HELD = 4                # xsGetUnitProperty: what a unit (or a resource pile) holds
PLAYERS = range(1, 7)
LANES = {p: 6 + (p - 2) * 8 for p in range(2, 7)}           # each computer player's row (y)
PILE_LABELS = ["P2 gold tree", "P3 stone bush", "P4 stone tree", "P5 tree", "P6 tree", "P1 gold fish"]

INSTRUCTIONS = """Crucible resource test, round 2. The map is revealed; nothing ends the game. Let it run about 5 \
minutes (speed it up if you like), then quit. Everyone starts working on their own.

Rows from the left corner, one allied player each:
P2 lumberjacks on trees switched to hold GOLD | P3 foragers on berry bushes switched to hold STONE | P4 lumberjacks \
on a tree type switched to STONE for the whole type | P5 normal lumberjacks, a script pays 10% of their wood as gold | \
P6 normal lumberjacks (control).

YOUR fishing boat works a fish switched to hold GOLD.

Watch: what do the gatherers carry, where do they drop it off, and what does each player receive? Select a tree, \
bush or fish to see what it holds. Everything is logged for the report."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def _paint(s, terrain: int, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            s.map_manager.get_tile(x=x, y=y).terrain_id = terrain


def xs_code(tracked: list[int]) -> str:
    """Record stockpiles and tracked piles every INTERVAL seconds, and pay player 5 a share of its wood as gold."""
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(PLAYERS), len(tracked), *tracked])
    stock = "".join(f"        xsWriteInt(xsPlayerAttribute(p, {a}));\n" for a in range(4))
    piles = "".join(f"    crucibleWritePile({u});\n" for u in tracked)
    return f"""// ---- crucible resource test, round 2 ----
float crucibleLastWood = 0.0;
float crucibleGoldOwed = 0.0;

void crucibleWritePile(int id = -1) {{
    int held = -1;
    int kind = -1;
    if (xsDoesUnitExist(id)) {{
        held = xsGetUnitProperty(id, {UNIT_ATTRIBUTE_HELD});
        kind = xsGetUnitAttribute(id, {STORAGE_TYPE});
    }}
    xsWriteInt(held);
    xsWriteInt(kind);
}}

rule crucibleResourceInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleResourceSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
    for (p = 1; < {len(PLAYERS) + 1}) {{
{stock}    }}
{piles}    xsCloseFile();
}}

rule crucibleConvertWoodToGold
    active
    minInterval 1
{{
    float wood = xsPlayerAttribute({CONVERT_PLAYER}, {WOOD_TOTAL});
    crucibleGoldOwed = crucibleGoldOwed + (wood - crucibleLastWood) * {CONVERT_SHARE};
    crucibleLastWood = wood;
    if (crucibleGoldOwed >= 1.0) {{
        int whole = crucibleGoldOwed;
        xsSetPlayerAttribute({CONVERT_PLAYER}, {GOLD}, xsPlayerAttribute({CONVERT_PLAYER}, {GOLD}) + whole);
        crucibleGoldOwed = crucibleGoldOwed - whole;
    }}
}}
"""


def _lumber_lane(s, p: int, tree: str) -> tuple[list[int], dict]:
    """A storage pit, a block of trees and three lumberjacks sent to them; returns the trees and the task."""
    y = LANES[p]
    _add(s, p, "STORAGE_PIT", 16, y)
    trees = [_add(s, 0, tree, 21 + i, y + j) for i in range(4) for j in (-1, 0, 1)]
    jacks = [_add(s, p, "VILLAGER_MALE", 19, y - 1 + i) for i in range(3)]
    return trees, {"type": "task_object", "source_player": p, "selected_object_ids": jacks,
                   "location_object_reference": trees[4]}


def build_mission(out: Path) -> tuple[Path, list[int], list[str]]:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = len(PLAYERS)
            for p in PLAYERS:
                fields = {"civilization": "GREEK", "starting_age": "CASTLE", "human": p == 1,
                          "food": 0, "wood": 0, "gold": 0, "stone": 0, "population_cap": 200}
                if p > 1:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            for p in PLAYERS:
                diplomacy_set(o.handle, p, [q for q in PLAYERS if q != p], "ALLY", mutual=False)
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            tasks, settings = [], []

            gold_trees, task = _lumber_lane(s, 2, "TREE_A")
            tasks.append(task)
            settings.append({"type": "modify_object_attribute", "source_player": 0, "selected_object_ids": gold_trees,
                             "object_attributes": STORAGE_TYPE, "operation": SET, "quantity": GOLD})
            tracked.append(gold_trees[4])

            y = LANES[3]
            _add(s, 3, "GRANARY", 16, y)
            bushes = [_add(s, 0, "FORAGE_BUSH", 21 + i * 2, y + j) for i in range(3) for j in (-1, 1)]
            foragers = [_add(s, 3, "VILLAGER_MALE", 19, y - 1 + i) for i in range(3)]
            tasks.append({"type": "task_object", "source_player": 3, "selected_object_ids": foragers,
                          "location_object_reference": bushes[0]})
            settings.append({"type": "modify_object_attribute", "source_player": 0, "selected_object_ids": bushes,
                             "object_attributes": STORAGE_TYPE, "operation": SET, "quantity": STONE})
            tracked.append(bushes[0])

            stone_trees, task = _lumber_lane(s, 4, "TREE_B")             # only P4's lane uses TREE_B
            tasks.append(task)
            settings.append({"type": "modify_attribute", "source_player": 0, "object_list_unit_id": "TREE_B",
                             "object_attributes": STORAGE_TYPE, "operation": SET, "quantity": STONE})
            tracked.append(stone_trees[4])

            for p in (5, 6):
                trees, task = _lumber_lane(s, p, "TREE_A")
                tasks.append(task)
                tracked.append(trees[4])

            # Player 1: water, a dock and a fishing boat on a gold fish.
            _paint(s, 23, (40, 36, SIZE - 1, SIZE - 1))                # WATER_DEEP
            _add(s, 1, "TOWN_CENTER", 10, 54)
            _add(s, 1, "DOCK", 38, 46)
            fish = _add(s, 0, "FISH5", 46, 46)
            boat = _add(s, 1, "FISHING_BOAT", 43, 48)
            tasks.append({"type": "task_object", "source_player": 1, "selected_object_ids": [boat],
                          "location_object_reference": fish})
            settings.append({"type": "modify_object_attribute", "source_player": 0, "selected_object_ids": [fish],
                             "object_attributes": STORAGE_TYPE, "operation": SET, "quantity": GOLD})
            tracked.append(fish)

            settings.append({"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1,
                             "quantity": 2, "operation": "SET"})
            ctx.trigger("Resource settings", [], settings)
            ctx.trigger("Start working", [{"type": "timer", "timer": 2}], tasks)
            ctx.xs(xs_code(tracked))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 22, "initial_player_view_y": 30})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{CAMPAIGN}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path, tracked, list(PILE_LABELS)
    finally:
        SESSIONS.close(o.handle)


def decode(data: bytes) -> dict:
    vals = list(struct.unpack_from(f"<{len(data) // 4}i", data))
    if len(vals) < 4 or vals[0] != MAGIC:
        raise ValueError("not a crucible resource test record")
    version, players, ntracked = vals[1], vals[2], vals[3]
    per_pile = 2 if version >= 2 else 1
    i = 4 + ntracked
    width = players * 4 + ntracked * per_pile
    samples = []
    while i + 2 + width <= len(vals) and vals[i] == TAG_SAMPLE:
        t, row = vals[i + 1], vals[i + 2:i + 2 + width]
        stock = {p + 1: dict(zip(("food", "wood", "stone", "gold"), row[p * 4:p * 4 + 4], strict=True))
                 for p in range(players)}
        rest = row[players * 4:]
        piles = [tuple(rest[k:k + per_pile]) for k in range(0, len(rest), per_pile)]
        samples.append({"t": t, "stock": stock, "piles": piles})
        i += 2 + width
    return {"version": version, "samples": samples}


def report(record: Path) -> str:
    """Each player's food/wood/stone/gold and each pile's amount (and resource type) per sample."""
    rec = decode(record.read_bytes())
    lines = []
    for s in rec["samples"]:
        stock = "  ".join(f"P{p} {v['food']}/{v['wood']}/{v['stone']}/{v['gold']}" for p, v in s["stock"].items())
        piles = "  ".join(f"{label} {'/'.join(map(str, pile))}" for label, pile in zip(PILE_LABELS, s["piles"], strict=False))
        lines.append(f"{s['t'] // 60:2}:{s['t'] % 60:02}  {stock}  |  {piles}")
    return "food/wood/stone/gold per player; piles: amount/resource type (0 food, 1 wood, 2 stone, 3 gold, 17 fish)\n" \
        + "\n".join(lines)
