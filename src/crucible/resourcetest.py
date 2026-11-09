"""The resource test: extreme gather values, a mismatched gather swap, trickles and generation.

A standalone scenario, `crucible_resource_test`, played from the Scenario lobby with the Crucible Test Data mod
picked as the Data Mod (it makes fishing boats take wood from fish). Each idea gets its own allied computer player, because the
multipliers are per player. Their villagers start working on their own; you watch.

| Player | Test |
|---|---|
| 1 (you) | A fishing boat beside fish. The data mod tells boats to take **wood** from fish: does it gather at all? |
| 2 | Stone miners, normal: the control |
| 3 | Stone miners with Stone Bonus 0 |
| 4 | Stone miners with Stone Bonus 10 (the game's own "resources last longer" multiplier) |
| 5 | Stone miners with work rate 0 |
| 6 | Generation: food 60, wood 1 (per second or per minute?) |
| 7 | Military Food Trickle 3, with 5 hoplites standing around |
| 8 | Lumberjacks with Chopping Gold Productivity 33 (chopping wood also gives gold) |

A script writes every player's stockpile and each pile's remaining amount every 10 seconds to
`<profile>/profile/crucible_resource_test.xsdat`; `crucible resource-report` prints it. It also posts a short
summary in chat every minute.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

CAMPAIGN = "crucible_resource_test"
SIZE = 64
MAGIC, VERSION, TAG_SAMPLE = 412320777, 1, 1
INTERVAL = 10
STONE_BONUS, WORK_RATE, CHOPPING_GOLD, MILITARY_FOOD = 79, 13, 266, 287
FOOD_GEN, WOOD_GEN = 230, 231
REVEAL_MAP, SET = 203, 1
STONE_MINERS = (124, 220)
UNIT_ATTRIBUTE_HELD = 4                # xsGetUnitProperty: what a unit (or a resource pile) holds
PLAYERS = range(1, 9)
LANES = {p: 6 + (p - 2) * 7 for p in range(2, 9)}           # each computer player's row (y)

INSTRUCTIONS = """Crucible resource test. Pick "Crucible Test Data" as the Data Mod in the lobby. The map is revealed; \
nothing ends the game. Let it run about 5 minutes (speed it up if you like), then quit.

Rows from the left corner, one allied player each:
P2 stone miners, normal (control) | P3 Stone Bonus 0 | P4 Stone Bonus 10 | P5 miners' work rate 0 | \
P6 generation: food 60, wood 1 | P7 military food trickle 3 (5 hoplites) | P8 lumberjacks, chopping gives gold 33.

Watch: do P3's and P5's miners gather anything? Does P4's mine last longer than P2's? How fast do P6's food and wood \
and P7's food grow? Does P8 get gold?

YOUR fishing boat: the data mod tells boats to take wood from fish. Click the boat on the fish: does it fish?

A summary is posted in chat every minute, and everything is logged for the report."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def _paint(s, terrain: int, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            s.map_manager.get_tile(x=x, y=y).terrain_id = terrain


def xs_code(tracked: list[int]) -> str:
    """Record every player's food, wood, stone and gold and each tracked pile's amount every INTERVAL seconds."""
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(PLAYERS), len(tracked), *tracked])
    stock = "".join(f"        xsWriteInt(xsPlayerAttribute(p, {a}));\n" for a in range(4))
    piles = "".join(f"    crucibleWritePile({u});\n" for u in tracked)
    chat = "".join(f'    xsChatData("{label}: %d", xsPlayerAttribute({p}, {a}));\n' for label, p, a in (
        ("P2 control stone", 2, 2), ("P3 bonus 0 stone", 3, 2), ("P4 bonus 10 stone", 4, 2),
        ("P5 rate 0 stone", 5, 2), ("P6 generation food", 6, 0), ("P6 generation wood", 6, 1),
        ("P7 military trickle food", 7, 0), ("P8 chopping gold", 8, 3), ("P8 wood", 8, 1), ("P1 food", 1, 0),
        ("P1 wood", 1, 1)))
    return f"""// ---- crucible resource test ----
void crucibleWritePile(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitProperty(id, {UNIT_ATTRIBUTE_HELD});
    }}
    xsWriteInt(v);
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

rule crucibleResourceChat
    active
    minInterval 60
{{
{chat}}}
"""


def build_mission(out: Path) -> tuple[Path, list[int], list[str]]:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked, labels = [], []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 8
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
            tasks = []

            # Players 2-5: three stone miners each, a mine and a storage pit side by side.
            for p in (2, 3, 4, 5):
                y = LANES[p]
                _add(s, p, "STORAGE_PIT", 16, y)
                mine = _add(s, 0, "STONE_MINE", 22, y)
                tracked.append(mine)
                labels.append(f"P{p} mine")
                miners = [_add(s, p, "VILLAGER_MALE", 19, y - 1 + i) for i in range(3)]
                tasks.append({"type": "task_object", "source_player": p, "selected_object_ids": miners,
                              "location_object_reference": mine})
            # Player 6: nothing to gather; player 7: soldiers; player 8: lumberjacks by a storage pit.
            for p in (6, 7):
                blocks.anchor(ctx, player=p, at=(2, LANES[p]))
            for i in range(5):
                _add(s, 7, "HOPLITE", 16 + i * 2, LANES[7])
            y = LANES[8]
            _add(s, 8, "STORAGE_PIT", 16, y)
            trees = [_add(s, 0, "TREE_A", 21 + i, y + j) for i in range(4) for j in (-1, 0, 1)]
            jacks = [_add(s, 8, "VILLAGER_MALE", 19, y - 1 + i) for i in range(3)]
            tasks.append({"type": "task_object", "source_player": 8, "selected_object_ids": jacks,
                          "location_object_reference": trees[4]})

            # Player 1: water with fish, a dock and a fishing boat.
            _paint(s, 23, (40, 36, SIZE - 1, SIZE - 1))                # WATER_DEEP
            _add(s, 1, "TOWN_CENTER", 10, 54)
            _add(s, 1, "DOCK", 38, 46)
            fish = _add(s, 0, "FISH5", 46, 46)
            tracked.append(fish)
            labels.append("P1 fish")
            _add(s, 1, "FISHING_BOAT", 43, 48)

            per_player = [
                {"type": "modify_resource", "source_player": 3, "tribute_list": STONE_BONUS, "operation": SET,
                 "quantity": 0},
                {"type": "modify_resource", "source_player": 4, "tribute_list": STONE_BONUS, "operation": SET,
                 "quantity": 10},
                {"type": "modify_resource", "source_player": 6, "tribute_list": FOOD_GEN, "operation": SET,
                 "quantity": 60},
                {"type": "modify_resource", "source_player": 6, "tribute_list": WOOD_GEN, "operation": SET,
                 "quantity": 1},
                {"type": "modify_resource", "source_player": 7, "tribute_list": MILITARY_FOOD, "operation": SET,
                 "quantity": 3},
                {"type": "modify_resource", "source_player": 8, "tribute_list": CHOPPING_GOLD, "operation": SET,
                 "quantity": 33},
                *({"type": "modify_attribute", "source_player": 5, "object_list_unit_id": uid,
                   "object_attributes": WORK_RATE, "operation": SET, "quantity": 0} for uid in STONE_MINERS),
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}]
            ctx.trigger("Resource settings", [], per_player)
            ctx.trigger("Start working", [{"type": "timer", "timer": 2}], tasks)
            ctx.xs(xs_code(tracked))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 22, "initial_player_view_y": 30})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{CAMPAIGN}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path, tracked, labels
    finally:
        SESSIONS.close(o.handle)


def decode(data: bytes) -> dict:
    vals = list(struct.unpack_from(f"<{len(data) // 4}i", data))
    if len(vals) < 4 or vals[0] != MAGIC:
        raise ValueError("not a crucible resource test record")
    players, ntracked = vals[2], vals[3]
    i = 4 + ntracked
    width = players * 4 + ntracked
    samples = []
    while i + 2 + width <= len(vals) and vals[i] == TAG_SAMPLE:
        t, row = vals[i + 1], vals[i + 2:i + 2 + width]
        stock = {p + 1: dict(zip(("food", "wood", "stone", "gold"), row[p * 4:p * 4 + 4], strict=True))
                 for p in range(players)}
        samples.append({"t": t, "stock": stock, "piles": row[players * 4:]})
        i += 2 + width
    return {"samples": samples}


PILE_LABELS = ["P2 mine", "P3 mine", "P4 mine", "P5 mine", "P1 fish"]      # build_mission's tracked order


def report(record: Path) -> str:
    rec = decode(record.read_bytes())
    labels = PILE_LABELS
    lines = [" time | P2 st  P3 st  P4 st  P5 st | P6 food P6 wood | P7 food | P8 wood P8 gold | P1 food P1 wood"
             " | " + " ".join(f"{label:>8}" for label in labels)]
    for s in rec["samples"]:
        st = s["stock"]
        lines.append(f" {s['t'] // 60:2}:{s['t'] % 60:02} | {st[2]['stone']:5} {st[3]['stone']:6} {st[4]['stone']:6}"
                     f" {st[5]['stone']:6} | {st[6]['food']:7} {st[6]['wood']:7} | {st[7]['food']:7} |"
                     f" {st[8]['wood']:7} {st[8]['gold']:7} | {st[1]['food']:7} {st[1]['wood']:7} | "
                     + " ".join(f"{v:8}" for v in s["piles"]))
    return "\n".join(lines)
