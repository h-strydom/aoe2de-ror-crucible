"""The combat test: friendly fire, splash size, projectiles, minimum and maximum range, trade shares.

A standalone scenario, `crucible_combat_test`, played from the Scenario lobby (no data mod needed; picking
Crucible Test Data is fine too). Player 1's test units face passive enemy targets (player 2) in lanes. Most changes
are made on one unit only (Modify Object Attribute), next to an unchanged control:

| Lane | Test |
|---|---|
| 1 | Stone Thrower with **friendly fire 0**; two of your hoplites stand among its targets |
| 2 | Stone Thrower unchanged, the same setup: the control for lanes 1 and 3 |
| 3 | Stone Thrower with **splash width 3** on a spread-out clump |
| 4 | Catapult firing a **ballista bolt** (projectile swapped on that catapult) |
| 5 | Catapult firing a projectile made **fast (x3) and flat** (arc 0) |
| 6 | Two Ballistas with an enemy right beside them: **minimum range 0** against the normal 3 |
| 7 | Two Hoplites on stand ground, an enemy 2.5 tiles away: **range 3** against the normal 0 |
| water | Your trade boat trades with an ally's dock; **trade shares 25%** food, wood and stone |

Everything starts on its own. A script logs hit points and your resources every 5 seconds to
`<profile>/profile/crucible_combat_test.xsdat`; `crucible combat-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_combat_test"
SIZE = 72
MAGIC, VERSION, TAG_SAMPLE = 412320888, 1, 1
INTERVAL = 5
# Object attributes
PROJECTILE_UNIT, MAX_RANGE, MIN_RANGE, BLAST_WIDTH, MOVEMENT_SPEED, PROJECTILE_ARC, FRIENDLY_FIRE = 16, 12, 20, 22, 5, \
    69, 119
TRADE_SHARES = (251, 252, 253)        # player attributes: Trade Food / Wood / Stone Percent
TRADE_INCOME = 101                    # player attribute: trade income so far
BOLT, SPARE_PROJECTILE = 367, 369     # ballista bolt; the Catapult Trireme's projectile (no land unit uses it)
REVEAL_MAP, SET = 203, 1
LANE_Y = {k: 6 + (k - 1) * 8 for k in range(1, 8)}
SHOOTER_X, TARGET_X = 8, 17

INSTRUCTIONS = """Crucible combat test. The map is revealed; nothing ends the game. Everything starts on its own: \
watch for 2-3 minutes, then quit. Enemy targets don't fight back.

Lanes from the left corner (your unit on the left, targets to its right):
1 Stone Thrower with FRIENDLY FIRE 0: two of your hoplites stand among the targets. Do they get hurt?
2 Stone Thrower unchanged, same setup: the control.
3 Stone Thrower with SPLASH WIDTH 3 on a spread-out clump: does it hit more than lane 2's would?
4 Catapult firing a BALLISTA BOLT: what does it fire, and does it still hurt?
5 Catapult firing a FAST (x3), FLAT projectile: does it look like a cannon shot?
6 Two Ballistas, an enemy right beside them: the first has MINIMUM RANGE 0, the second the normal 3. Who fires?
7 Two Hoplites on stand ground, an enemy 2.5 tiles away: the first has RANGE 3. Does it attack without moving?

WATER: your trade boat trades with your ally's dock. Trade shares are set to 25% food, wood and stone: do you get \
food, wood or stone as well as gold?

Hit points and your resources are logged for the report."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def _paint(s, terrain: int, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            s.map_manager.get_tile(x=x, y=y).terrain_id = terrain


def xs_code(tracked: list[int]) -> str:
    """Every INTERVAL seconds: player 1's food, wood, stone, gold and trade income, then each tracked unit's HP."""
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(tracked), *tracked])
    hp = "".join(f"    crucibleWriteHp({u});\n" for u in tracked)
    stock = "".join(f"    xsWriteInt(xsPlayerAttribute(1, {a}));\n" for a in (0, 1, 2, 3, TRADE_INCOME))
    return f"""// ---- crucible combat test ----
void crucibleWriteHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

rule crucibleCombatInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleCombatSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
{stock}{hp}    xsCloseFile();
}}
"""


def build(out: Path) -> tuple[Path, list[tuple[str, int]]]:
    """Write the scenario; returns its path and the tracked units (label, reference id) in log order."""
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked: list[tuple[str, int]] = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 3
            for p in (1, 2, 3):
                fields = {"civilization": "GREEK", "starting_age": "CASTLE", "human": p == 1,
                          "food": 0, "wood": 0, "gold": 0, "stone": 0, "population_cap": 200}
                if p > 1:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            diplomacy_set(o.handle, 1, [3], "ALLY")
            diplomacy_set(o.handle, 2, [3], "NEUTRAL")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            mine = {"type": "modify_object_attribute", "source_player": 1, "operation": SET}
            settings, targets, mine_units = [], [], []

            def clump(lane: int, spacing: float, own: int = 0) -> list[int]:
                """Five passive enemy clubmen (plus `own` of your hoplites among them) at a lane's target spot."""
                y = LANE_Y[lane]
                spots = [(0, 0), (spacing, 0), (-spacing, 0), (0, spacing), (0, -spacing)]
                ids = [_add(s, 2, "CLUBMAN", TARGET_X + dx, y + dy) for dx, dy in spots]
                targets.extend(ids)
                for k in range(own):
                    h = _add(s, 1, "HOPLITE", TARGET_X + 0.7 * (1 if k else -1), y + 0.7)
                    mine_units.append(h)
                    tracked.append((f"L{lane} own hoplite {k + 1}", h))
                tracked.append((f"L{lane} centre target", ids[0]))
                return ids

            for lane, change in ((1, (FRIENDLY_FIRE, 0)), (2, None), (3, (BLAST_WIDTH, 3))):
                thrower = _add(s, 1, "STONE_THROWER", SHOOTER_X, LANE_Y[lane])
                mine_units.append(thrower)
                ids = clump(lane, 2.0 if lane == 3 else 0.8, own=2 if lane in (1, 2) else 0)
                if lane == 3:
                    tracked.extend((f"L3 outer target {k}", i) for k, i in enumerate(ids[1:], start=1))
                if change:
                    settings.append({**mine, "selected_object_ids": [thrower], "object_attributes": change[0],
                                     "quantity": change[1]})
                settings.append({"type": "task_object", "source_player": 1, "selected_object_ids": [thrower],
                                 "location_object_reference": ids[0]})

            for lane, projectile in ((4, BOLT), (5, SPARE_PROJECTILE)):
                cat = _add(s, 1, "CATAPULT", SHOOTER_X, LANE_Y[lane])
                mine_units.append(cat)
                target = _add(s, 2, "WAR_ELEPHANT", TARGET_X, LANE_Y[lane])
                targets.append(target)
                tracked.append((f"L{lane} target", target))
                settings.append({**mine, "selected_object_ids": [cat], "object_attributes": PROJECTILE_UNIT,
                                 "quantity": projectile})
                settings.append({"type": "task_object", "source_player": 1, "selected_object_ids": [cat],
                                 "location_object_reference": target})
            settings += [{"type": "modify_attribute", "source_player": 1, "object_list_unit_id": SPARE_PROJECTILE,
                          "object_attributes": MOVEMENT_SPEED, "operation": SET, "quantity": 10.5},
                         {"type": "modify_attribute", "source_player": 1, "object_list_unit_id": SPARE_PROJECTILE,
                          "object_attributes": PROJECTILE_ARC, "operation": SET, "quantity": 0}]

            for lane, unit, change, gap in ((6, "BALLISTA", (MIN_RANGE, 0), 1.5), (7, "HOPLITE", (MAX_RANGE, 3), 2.5)):
                for k, x in enumerate((SHOOTER_X, SHOOTER_X + 14)):        # changed one, then the control
                    me = _add(s, 1, unit, x, LANE_Y[lane])
                    mine_units.append(me)
                    target = _add(s, 2, "WAR_ELEPHANT", x + gap, LANE_Y[lane])
                    targets.append(target)
                    tracked.append((f"L{lane} {'changed' if k == 0 else 'control'} target", target))
                    if k == 0:
                        settings.append({**mine, "selected_object_ids": [me], "object_attributes": change[0],
                                         "quantity": change[1]})

            # Water: player 1's dock and trade boat, player 3's dock across the water.
            _paint(s, 23, (48, 0, SIZE - 1, SIZE - 1))
            _add(s, 1, "DOCK", 46, 10)
            ally_dock = _add(s, 3, "DOCK", 46, 62)
            boat = _add(s, 1, "TRADE_BOAT", 50, 12)
            settings += [{"type": "modify_resource", "source_player": 1, "tribute_list": a, "operation": SET,
                          "quantity": 25} for a in TRADE_SHARES]
            trade = {"type": "task_object", "source_player": 1, "selected_object_ids": [boat],
                     "location_object_reference": ally_dock}

            _add(s, 1, "TOWN_CENTER", 34, 66)
            blocks.anchor(ctx, player=2, at=(70, 2))
            blocks.anchor(ctx, player=3, at=(70, 70))
            stand = [{"type": "change_object_stance", "source_player": 1, "selected_object_ids": mine_units,
                      "attack_stance": "STAND_GROUND"},
                     {"type": "change_object_stance", "source_player": 2, "selected_object_ids": targets,
                      "attack_stance": "NO_ATTACK_STANCE"}]
            ctx.trigger("Combat settings", [], [*stand, {"type": "modify_resource", "tribute_list": REVEAL_MAP,
                                                         "source_player": 1, "quantity": 2, "operation": "SET"}])
            ctx.trigger("Start", [{"type": "timer", "timer": 3}], [*settings, trade])
            ctx.xs(xs_code([u for _, u in tracked]))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 14, "initial_player_view_y": 28})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path, tracked
    finally:
        SESSIONS.close(o.handle)


def labels() -> list[str]:
    """The tracked units' labels, in log order (rebuilds the scenario in a temporary folder)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        return [label for label, _ in build(Path(tmp))[1]]


def decode(data: bytes) -> dict:
    vals = list(struct.unpack_from(f"<{len(data) // 4}i", data))
    if len(vals) < 3 or vals[0] != MAGIC:
        raise ValueError("not a crucible combat test record")
    n = vals[2]
    i = 3 + n
    width = 5 + n
    samples = []
    while i + 2 + width <= len(vals) and vals[i] == TAG_SAMPLE:
        t, row = vals[i + 1], vals[i + 2:i + 2 + width]
        samples.append({"t": t, "stock": dict(zip(("food", "wood", "stone", "gold", "trade"), row[:5], strict=True)),
                        "hp": row[5:]})
        i += 2 + width
    return {"tracked": vals[3:3 + n], "samples": samples}


def report(record: Path, labels: list[str]) -> str:
    rec = decode(record.read_bytes())
    names = labels if len(labels) == len(rec["tracked"]) else [f"unit {u}" for u in rec["tracked"]]
    lines = ["HP per sample (-1 = dead); player 1 food/wood/stone/gold and trade income", "units: " +
             ", ".join(f"{k}={n}" for k, n in enumerate(names))]
    for s in rec["samples"]:
        st = s["stock"]
        lines.append(f"{s['t'] // 60:2}:{s['t'] % 60:02}  P1 {st['food']}/{st['wood']}/{st['stone']}/{st['gold']} "
                     f"trade {st['trade']}  |  " + " ".join(f"{k}:{v}" for k, v in enumerate(s["hp"])))
    return "\n".join(lines)
