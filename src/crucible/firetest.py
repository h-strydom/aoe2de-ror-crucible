"""The friendly fire test: why didn't Friendly Fire Damage 0 on one Stone Thrower stop it hurting your own units?

Combat test (2026-11-09): your hoplites among a Stone Thrower's targets lost the same hit points whether its
Friendly Fire Damage (119) was 0 or unchanged. AoE2 does this as a researched bonus on whole unit types (Jurchens:
multiply 119 by 0.5 for archers, infantry, cavalry, siege, ships...). Possible causes: only the unit type is read,
not one unit; a 0 counts as "not set"; or only the projectile's value counts.

Every lane is self-checking: a siege unit fires into passive enemies with two of your hoplites among them. Friendly
fire works if your hoplites stay unhurt while the enemies around them take damage. Lanes are 16 tiles apart, beyond
any of these units' range.

| Lane | Change |
|---|---|
| 1 | Stone Thrower unchanged: the control |
| 2 | Stone Thrower, 0.01 on that unit only (is 0 special?) |
| 3 | Catapults, 0 for the whole type |
| 4 | Heavy Catapults, 0.01 for the whole type |
| 5 | Stone Thrower firing its own projectile (the Catapult Trireme's), whose type has friendly fire 0 |
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_friendly_fire_test"
SIZE = 96
MAGIC, VERSION, TAG_SAMPLE = 412320999, 1, 1
INTERVAL = 5
FRIENDLY_FIRE, PROJECTILE_UNIT = 119, 16
SPARE_PROJECTILE = 369                # the Catapult Trireme's projectile: no land unit uses it
REVEAL_MAP, SET = 203, 1
LANES = {1: ("STONE_THROWER", "unit", None), 2: ("STONE_THROWER", "unit", 0.01),
         3: ("CATAPULT", "type", 0), 4: ("HEAVY_CATAPULT", "type", 0.01), 5: ("STONE_THROWER", "projectile", 0)}
LANE_Y = {k: 8 + (k - 1) * 16 for k in LANES}
SHOOTER_X, TARGET_X = 10, 20

INSTRUCTIONS = """Crucible friendly fire test. The map is revealed; nothing ends the game. Everything starts on its \
own: watch for about 1 minute, then quit. Enemy targets don't fight back.

Each lane: a siege unit fires at passive enemies with two of YOUR hoplites standing among them. Friendly fire is \
off if your hoplites stay unhurt while the enemies around them take damage.

1 Stone Thrower unchanged (control) | 2 Stone Thrower, 0.01 on that unit only | 3 Catapults, 0 for the whole type | \
4 Heavy Catapults, 0.01 for the whole type | 5 Stone Thrower firing a separate projectile whose type has 0.

Hit points are logged for the report."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(tracked: list[int]) -> str:
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(tracked), *tracked])
    hp = "".join(f"    crucibleWriteHp({u});\n" for u in tracked)
    return f"""// ---- crucible friendly fire test ----
void crucibleWriteHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

rule crucibleFireInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleFireSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
{hp}    xsCloseFile();
}}
"""


def build(out: Path) -> tuple[Path, list[tuple[str, int]]]:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked: list[tuple[str, int]] = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            for p in (1, 2):
                fields = {"civilization": "GREEK", "starting_age": "CASTLE", "human": p == 1,
                          "population_cap": 200}
                if p == 2:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            mine, enemies, settings = [], [], []
            for lane, (unit, scope, value) in LANES.items():
                y = LANE_Y[lane]
                shooter = _add(s, 1, unit, SHOOTER_X, y)
                mine.append(shooter)
                clump = [_add(s, 2, "CLUBMAN", TARGET_X + dx, y + dy)
                         for dx, dy in ((0, 0), (0.8, 0), (-0.8, 0), (0, 0.8), (0, -0.8))]
                enemies.extend(clump)
                own = [_add(s, 1, "HOPLITE", TARGET_X + dx, y + 0.6) for dx in (-0.6, 0.6)]
                mine.extend(own)
                tracked += [(f"L{lane} own hoplite 1", own[0]), (f"L{lane} own hoplite 2", own[1]),
                            (f"L{lane} enemy centre", clump[0]), (f"L{lane} enemy side", clump[1])]
                if scope == "unit" and value is not None:
                    settings.append({"type": "modify_object_attribute", "source_player": 1,
                                     "selected_object_ids": [shooter], "object_attributes": FRIENDLY_FIRE,
                                     "operation": SET, "quantity": value})
                elif scope == "type":
                    settings.append({"type": "modify_attribute", "source_player": 1, "object_list_unit_id": unit,
                                     "object_attributes": FRIENDLY_FIRE, "operation": SET, "quantity": value})
                elif scope == "projectile":
                    settings += [{"type": "modify_object_attribute", "source_player": 1,
                                  "selected_object_ids": [shooter], "object_attributes": PROJECTILE_UNIT,
                                  "operation": SET, "quantity": SPARE_PROJECTILE},
                                 {"type": "modify_attribute", "source_player": 1,
                                  "object_list_unit_id": SPARE_PROJECTILE, "object_attributes": FRIENDLY_FIRE,
                                  "operation": SET, "quantity": value}]
                settings.append({"type": "task_object", "source_player": 1, "selected_object_ids": [shooter],
                                 "location_object_reference": clump[0]})
            _add(s, 1, "TOWN_CENTER", 80, 80)
            blocks.anchor(ctx, player=2, at=(94, 2))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 1, "selected_object_ids": mine,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": enemies,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}])
            ctx.trigger("Start", [{"type": "timer", "timer": 3}], settings)
            ctx.xs(xs_code([u for _, u in tracked]))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 16, "initial_player_view_y": 40})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path, tracked
    finally:
        SESSIONS.close(o.handle)


def labels() -> list[str]:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        return [label for label, _ in build(Path(tmp))[1]]


def decode(data: bytes) -> dict:
    vals = list(struct.unpack_from(f"<{len(data) // 4}i", data))
    if len(vals) < 3 or vals[0] != MAGIC:
        raise ValueError("not a crucible friendly fire test record")
    n = vals[2]
    i = 3 + n
    samples = []
    while i + 2 + n <= len(vals) and vals[i] == TAG_SAMPLE:
        samples.append({"t": vals[i + 1], "hp": vals[i + 2:i + 2 + n]})
        i += 2 + n
    return {"tracked": vals[3:3 + n], "samples": samples}


def report(record: Path, names: list[str]) -> str:
    """Per lane: own hoplites' and enemies' hit points over time."""
    rec = decode(record.read_bytes())
    lines = []
    for lane in LANES:
        cols = [k for k, n in enumerate(names) if n.startswith(f"L{lane} ")]
        lines.append(f"Lane {lane} ({LANES[lane][0]}, {LANES[lane][1]}, {LANES[lane][2]}): "
                     + ", ".join(names[k][3:] for k in cols))
        for s in rec["samples"]:
            lines.append(f"   {s['t'] // 60}:{s['t'] % 60:02}  " + "  ".join(f"{s['hp'][k]:4}" for k in cols))
    return "\n".join(lines)
