"""Map tricks (`crucible_map_tricks`, with the Crucible Test Data mod): the engine test map's open questions, made
measurable.

- **An unbuildable line over any terrain.** Round 1 (Flags, the data mod's build blockers, a Rock 1 overlay layer)
  left every line buildable. Round 2: one-tile lines whose base terrain is unbuildable (Rock 1, Quicksand, Bogland)
  with the band's own terrain (grass, dirt, desert, road) as the overlay layer, plus plain Rock 1. Can villagers walk
  across, can anything be built on them, and do the layered ones look like the ground around them?
- **Safe zones.** Inside a square your units can't be attacked; outside they can. Zone A: a looping trigger enables
  attackable around it, then disables it inside (area effects). Zone B: a script sets each Hoplite's
  `cUnitAttackable` by its position (round 2: nothing inside was attacked). Round 3: from 0:12 a Stone Thrower per
  zone attacks the ground at the zone's centre; the armies attack at 1:30. Does ground-aimed splash get through?
- **Doubled resources.** Three gold mines (500 each): A doubled by trigger (Modify Object Attribute 21 = 1000), B by
  script (`cUnitAttributeHeld` x 2), C untouched; logged.
- **Formations.** Three groups of your units march right at 0:30: A in line formation, B in box formation (Task
  Object formation, then a group move), C just moves.
- **Pseudo multi-choice decisions.** At 0:10 three decision popups appear at once (A/B, C/D, E/F). The first pick
  switches off the other options' triggers. Do the popups stack? Does picking one close the others?

A script logs the mines' amounts and the safe zone Hoplites' HP every 5 s to
`<profile>/profile/crucible_map_tricks.xsdat`; `crucible map-tricks-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set


NAME = "crucible_map_tricks"
SIZE = 80
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322005, 3, 1, 5
REVEAL_MAP, SET, STORAGE_1, HOPLITE = 203, 1, 21, 93
BANDS = ((6, 15, 0), (16, 25, 6), (26, 35, 14), (36, 46, 24))     # x from, x to, terrain: grass, dirt, desert, road
# Round 1 (Flags, build blockers, a Rock 1 overlay layer): all buildable; the layer is visual only. Round 2: the base
# terrain decides, so the lines are an unbuildable base terrain (RoR's data allows no buildings on Rock 1, Quicksand,
# Bogland) with the band's terrain as the overlay layer, plus Rock 1 with no layer as the control.
ROCK_1, QUICKSAND, BOGLAND = 40, 46, 101
STRIPS = {"Rock 1 + layer": (ROCK_1, True), "Quicksand + layer": (QUICKSAND, True),
          "Bogland + layer": (BOGLAND, True), "Rock 1, no layer": (ROCK_1, False)}
STRIP_X, STRIP_YS = (6, 46), (6, 10, 14, 18)
ZONE_A, ZONE_B = (52, 6, 62, 16), (52, 26, 62, 36)
GOLD_MINE_AMOUNT = 500
LINE_FORMATION, BOX_FORMATION, MOVE, ATTACK_GROUND = 18, 19, 1, 6
# Round 3: a Stone Thrower per zone bombards the ground at the zone's centre from 0:12 (attack-ground aims at a spot,
# not a unit); the armies wait until 1:30, so damage inside before then can only be ground splash.
GROUND_ATTACK_AT, ARMY_AT = 12, 90
DECISIONS = ((1, "First choice", "A", "B"), (2, "Second choice", "C", "D"), (3, "Third choice", "E", "F"))

INSTRUCTIONS = """Crucible map tricks. Pick "Crucible Test Data" as the Data Mod. The map is revealed; \
Nothing ends the game.

UNBUILDABLE LINES (top left), round 2, top to bottom: Rock 1, Quicksand and Bogland underneath with the band's own \
terrain painted on top (grass, dirt, desert, road), then plain Rock 1. Do the top three look like the ground around \
them? With your villagers: can you walk across each line, and can you place a House or a wall ON it anywhere?
SAFE ZONES (right), round 3: from 0:12 an enemy Stone Thrower bombards the GROUND in the middle of each zone \
(attack-ground: aimed at a spot, not a unit). Do your Hoplites inside lose HP from the splash? Leave them where they \
are. At 1:30 the armies attack as before. Zone A (top) is the trigger version, zone B (below) the script version.
DOUBLED RESOURCES (left): three gold mines; the report shows their amounts (A trigger, B script, C control).
FORMATIONS (bottom): at 0:30 three groups march right: A in line formation, B in box, C plain. Do A and B keep a \
formation and arrive together?
DECISIONS: at 0:10 three choice popups appear at once. Do they stack? Pick one: do the others close, and does chat \
name your pick (later picks should do nothing)?"""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(mines: tuple[int, int, int], doubled: int, zone_b: tuple[int, int, int, int],
            tracked: list[int]) -> str:
    x1, y1, x2, y2 = zone_b
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(tracked), *tracked])
    amounts = "".join(f"    crucibleMapAmount({m});\n" for m in mines)
    hp = "".join(f"    crucibleMapHp({u});\n" for u in tracked)
    return f"""// ---- crucible map tricks ----
void crucibleMapHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

void crucibleMapAmount(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitProperty(id, cUnitAttributeHeld);
    }}
    xsWriteInt(v);
}}

rule crucibleMapInit
    active
    highFrequency
{{
    // Gold mine B: doubled by script.
    xsSetUnitProperty({doubled}, cUnitAttributeHeld, 2.0 * xsGetUnitProperty({doubled}, cUnitAttributeHeld));
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

// Safe zone B: each Hoplite of player 1 is attackable only outside the square.
rule crucibleSafeZoneB
    active
    minInterval 1
{{
    int list = xsGetPlayerUnitIds(1, {HOPLITE});
    for (i = 0; < xsArrayGetSize(list)) {{
        int id = xsArrayGetInt(list, i);
        if (xsGetUnitHitpoints(id) > 0) {{
            vector p = xsGetUnitPosition(id);
            float x = xsVectorGetX(p);
            float y = xsVectorGetY(p);
            if ((x >= {x1}.0) && (x <= {x2 + 1}.0) && (y >= {y1}.0) && (y <= {y2 + 1}.0)) {{
                xsSetUnitProperty(id, cUnitAttackable, 0);
            }} else {{
                xsSetUnitProperty(id, cUnitAttackable, 1);
            }}
        }}
    }}
}}

rule crucibleMapSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
{amounts}{hp}    xsCloseFile();
}}
"""


def build(out: Path) -> tuple[Path, list[tuple[str, int]]]:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked: list[tuple[str, int]] = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": True,
                                     "food": 2000, "wood": 2000, "gold": 2000, "stone": 2000, "population_cap": 200})
            player_set(o.handle, 2, {"civilization": "PERSIAN", "starting_age": "IMPERIAL", "ai": "none"})
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)

            # Unbuildable lines over terrain bands.
            for x_from, x_to, terrain in BANDS:
                for x in range(x_from, x_to + 1):
                    for y in range(3, 22):
                        s.map_manager.get_tile(x=x, y=y).terrain_id = terrain
            # Round 2: the base terrain is an unbuildable one; the overlay layer shows the band's own terrain.
            for (name, (base, layered)), y in zip(STRIPS.items(), STRIP_YS):
                for x_from, x_to, terrain in BANDS:
                    for x in range(x_from, x_to + 1):
                        tile = s.map_manager.get_tile(x=x, y=y)
                        tile.terrain_id = base
                        if layered:
                            tile.layer = terrain
            for k in range(6):
                _add(s, 1, "VILLAGER_MALE", 8 + k * 3, 24)

            # Safe zones: three Hoplites inside each, one outside; an enemy army for each.
            armies, bombards = [], []
            for label, (x1, y1, x2, y2) in (("A trigger", ZONE_A), ("B script", ZONE_B)):
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                for road_x in range(x1, x2 + 1):            # a road border to see the square
                    for road_y in (y1, y2):
                        s.map_manager.get_tile(x=road_x, y=road_y).terrain_id = 24
                for road_y in range(y1, y2 + 1):
                    for road_x in (x1, x2):
                        s.map_manager.get_tile(x=road_x, y=road_y).terrain_id = 24
                for k in range(3):
                    tracked.append((f"zone {label}: inside {k + 1}", _add(s, 1, "HOPLITE", cx - 1 + k, cy)))
                tracked.append((f"zone {label}: outside", _add(s, 1, "HOPLITE", x2 + 3, cy)))
                army = ([_add(s, 2, "SHORT_SWORDSMAN", 72, cy - 2 + k * 2) for k in range(3)]
                        + [_add(s, 2, "BOWMAN", 75, cy - 1 + k * 2) for k in range(2)]
                        + [_add(s, 2, "STONE_THROWER", 77, cy)])
                armies.append((army, (cx, cy)))
                bombards.append((_add(s, 2, "STONE_THROWER", x2 + 7, cy), (cx, cy)))

            # Gold mines: A doubled by trigger, B by script, C control.
            mines = tuple(_add(s, 0, "GOLD_MINE", 8 + k * 6, 32) for k in range(3))

            # Formations: three groups.
            groups = []
            for k, y in enumerate((44, 54, 64)):
                g = ([_add(s, 1, "HOPLITE", 6 + dx, y) for dx in (0, 1.5, 3)]
                     + [_add(s, 1, "BOWMAN", 6 + dx, y + 2) for dx in (0, 1.5, 3)]
                     + [_add(s, 1, "CAVALRY", 6 + dx, y + 4) for dx in (0, 2)])
                groups.append((g, y))

            _add(s, 1, "TOWN_CENTER", 40, 74)
            blocks.anchor(ctx, player=2, at=(78, 78))
            ax1, ay1, ax2, ay2 = ZONE_A
            ctx.trigger("Setup", [], [
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"},
                {"type": "modify_object_attribute", "source_player": 0, "selected_object_ids": [mines[0]],
                 "object_attributes": STORAGE_1, "operation": SET, "quantity": 2 * GOLD_MINE_AMOUNT}])
            ctx.trigger("Safe zone A", [{"type": "timer", "timer": 1}], [
                {"type": "enable_unit_attackable", "source_player": 1, "area": [ax1 - 6, ay1 - 4, ax2 + 8, ay2 + 4]},
                {"type": "disable_unit_attackable", "source_player": 1, "area": [ax1, ay1, ax2, ay2]}],
                looping=True)
            ctx.trigger("Ground attack", [{"type": "timer", "timer": GROUND_ATTACK_AT}], [
                {"type": "task_object", "source_player": 2, "selected_object_ids": [thrower],
                 "action_type": ATTACK_GROUND, "location": list(spot)} for thrower, spot in bombards])
            ctx.trigger("Enemy attack", [{"type": "timer", "timer": ARMY_AT}], [
                {"type": "attack_move", "source_player": 2, "selected_object_ids": army, "location": list(spot)}
                for army, spot in armies])
            march = []
            for (g, y), formation in zip(groups, (LINE_FORMATION, BOX_FORMATION, None)):
                if formation:
                    march.append({"type": "task_object", "source_player": 1, "selected_object_ids": g,
                                  "action_type": formation})
                march.append({"type": "task_object", "source_player": 1, "selected_object_ids": g,
                              "action_type": MOVE, "location": [60, y + 2], "issue_group_command": 1})
            ctx.trigger("March", [{"type": "timer", "timer": 30}], march)

            # Decisions: three at once; the first pick switches off every other option.
            names = [f"Decision {did} option {opt}" for did, *_ in DECISIONS for opt in (1, 2)]
            ctx.trigger("Decisions", [{"type": "timer", "timer": 10}], [
                {"type": "create_decision", "decision_id": did, "message": prompt, "message_option1": a,
                 "message_option2": b} for did, prompt, a, b in DECISIONS])
            options = []                                 # one batch: they name each other
            for did, _, a, b in DECISIONS:
                for opt, pick in ((1, a), (2, b)):
                    me = f"Decision {did} option {opt}"
                    options.append({"name": me, "conditions": [{"type": "decision_triggered", "decision_id": did,
                                                                "decision_option": opt}],
                                    "effects": [{"type": "send_chat", "source_player": 1, "message": f"Picked {pick}"},
                                                *({"type": "deactivate_trigger", "trigger_id": other}
                                                  for other in names if other != me)]})
            ctx.triggers(*options)
            ctx.xs(xs_code(mines, mines[1], ZONE_B, [u for _, u in tracked]))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 26, "initial_player_view_y": 20})
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


def report(record: Path, names: list[str]) -> str:
    vals = list(struct.unpack_from(f"<{record.stat().st_size // 4}i", record.read_bytes()))
    if vals[0] != MAGIC:
        raise ValueError("not a crucible map tricks record")
    n = vals[2]
    i, width = 3 + n, 2 + 3 + n
    samples = []
    while i + width <= len(vals) and vals[i] == TAG_SAMPLE:
        samples.append(vals[i + 1:i + width])
        i += width
    if not samples:
        return "no samples recorded"
    picks = [r for r in samples if r[0] in (5, 10, 20, 25, 30, 45, 60, 90, 120, 180)] or samples
    rows = ["".ljust(30) + "".join(f"{r[0] // 60}:{r[0] % 60:02}".rjust(7) for r in picks)]
    for k, label in enumerate(("gold mine A (trigger x2)", "gold mine B (script x2)", "gold mine C (control)")):
        rows.append(label.ljust(30) + "".join(str(r[1 + k]).rjust(7) for r in picks))
    for k, label in enumerate(names[:n]):
        rows.append(label[:29].ljust(30) + "".join(str(r[4 + k]).rjust(7) for r in picks))
    return "\n".join(rows)
