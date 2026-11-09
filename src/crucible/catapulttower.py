"""A stuck-together catapult tower: towers that fire a Stone Thrower's stone with its damage.

A standalone scenario, `crucible_catapult_tower`, to look at. Every tower type player 1 owns (Watch, Sentry, Guard,
Ballista Tower) gets, for the whole type, so towers already placed and any you build:
- projectile: the catapult stone (656), arced;
- reload 5.4 s, range 10;
- splash width 0.8 at Blast Attack Level 6 (splash hits enemies only: the friendly fire fix);
- the arrow's pierce attack set to 0.

The Stone Thrower's attack (50 melee, +140 vs buildings) is what didn't land in the first two looks (stones splashed
but did minimum damage, with Set and then with Add for the whole type). So each tower now gets it a different way,
and a script logs every tower's real attack values and its target's hit points:

| Tower | How it gets 50 melee and 140 vs buildings |
|---|---|
| Watch | Modify Attribute, Add, for the whole type |
| Sentry | Modify Attribute, Set, for the whole type |
| Guard | Modify Object Attribute, Add, on that tower only |
| Ballista | Change Object Attack (its own effect), Add, on that tower only |
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_catapult_tower"
SIZE = 48
TOWERS = ("WATCH_TOWER", "SENTRY_TOWER", "GUARD_TOWER", "BALLISTA_TOWER")
METHODS = {"WATCH_TOWER": "type add", "SENTRY_TOWER": "type set", "GUARD_TOWER": "object add",
           "BALLISTA_TOWER": "change attack"}
ATTACK, RELOAD, MAX_RANGE, SHOWN_RANGE, PROJECTILE_UNIT, BLAST_WIDTH, BLAST_LEVEL = 9, 10, 12, 47, 16, 22, 44
CATAPULT_STONE = 656
PIERCE, MELEE, BUILDINGS = 3, 4, 11                # attack classes
STONE_THROWER = {"melee": 50, "buildings": 140, "reload": 5.375, "range": 10, "blast": 0.8, "level": 6}
REVEAL_MAP, SET, ADD = 203, 1, 2
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412321111, 1, 1, 5

INSTRUCTIONS = """Crucible catapult tower. Every tower you own fires a Stone Thrower's stone with its reload, range \
and splash (splash only hurts enemies). Each tower gets the Stone Thrower's damage (50 melee, +140 vs buildings) a \
different way, from the left: Watch (Add, whole type), Sentry (Set, whole type), Guard (Add, that tower), Ballista \
(Change Object Attack, that tower). Which ones hit hard? Each tower's real attack values are logged. Enemies don't \
fight back. Nothing ends the game; a minute is enough."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def tower_effects(player: int = 1, towers=TOWERS) -> list[dict]:
    """The settings every catapult tower type shares (not its melee and building attack)."""
    out = []
    v = STONE_THROWER
    for tower in towers:
        mod = {"type": "modify_attribute", "source_player": player, "object_list_unit_id": tower, "operation": SET}
        out += [
            {**mod, "object_attributes": PROJECTILE_UNIT, "quantity": CATAPULT_STONE},
            {**mod, "object_attributes": ATTACK, "armour_attack_class": PIERCE, "armour_attack_quantity": 0},
            {**mod, "object_attributes": RELOAD, "quantity": v["reload"]},
            {**mod, "object_attributes": MAX_RANGE, "quantity": v["range"]},
            {**mod, "object_attributes": SHOWN_RANGE, "quantity": v["range"]},
            {**mod, "object_attributes": BLAST_WIDTH, "quantity": v["blast"]},
            {**mod, "object_attributes": BLAST_LEVEL, "quantity": v["level"]},
        ]
    return out


def attack_effects(tower: str, method: str, ref: int, player: int = 1) -> list[dict]:
    """The Stone Thrower's melee and building attack, given to a tower by one method."""
    out = []
    for cls, amount in ((MELEE, STONE_THROWER["melee"]), (BUILDINGS, STONE_THROWER["buildings"])):
        aa = {"armour_attack_class": cls, "armour_attack_quantity": amount}
        if method in ("type add", "type set"):
            out.append({"type": "modify_attribute", "source_player": player, "object_list_unit_id": tower,
                        "object_attributes": ATTACK, "operation": ADD if method == "type add" else SET, **aa})
        elif method == "object add":
            out.append({"type": "modify_object_attribute", "source_player": player, "selected_object_ids": [ref],
                        "object_attributes": ATTACK, "operation": ADD, **aa})
        else:
            out.append({"type": "change_object_attack", "source_player": player, "selected_object_ids": [ref],
                        "operation": ADD, **aa})
    return out


def xs_code(towers: list[int], targets: list[int]) -> str:
    """Every INTERVAL seconds: each tower's pierce, melee and building attack, and each target's hit points."""
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(towers), *towers, *targets])
    rows = "".join(f"    crucibleWriteTower({t}, {g});\n" for t, g in zip(towers, targets, strict=True))
    return f"""// ---- crucible catapult tower ----
void crucibleWriteTower(int tower = -1, int target = -1) {{
    int pierce = -1;
    int melee = -1;
    int buildings = -1;
    int hp = -1;
    if (xsDoesUnitExist(tower)) {{
        pierce = xsGetUnitAttribute(tower, {ATTACK}, {PIERCE});
        melee = xsGetUnitAttribute(tower, {ATTACK}, {MELEE});
        buildings = xsGetUnitAttribute(tower, {ATTACK}, {BUILDINGS});
    }}
    if (xsDoesUnitExist(target)) {{
        hp = xsGetUnitHitpoints(target);
    }}
    xsWriteInt(pierce);
    xsWriteInt(melee);
    xsWriteInt(buildings);
    xsWriteInt(hp);
}}

rule crucibleTowerInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleTowerSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
{rows}    xsCloseFile();
}}
"""


def build(out: Path) -> Path:
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
            towers, targets, attacks = [], [], []
            for k, tower in enumerate(TOWERS):
                ref = _add(s, 1, tower, 6 + k * 11, 14)
                towers.append(ref)
                targets.append(_add(s, 2, "WAR_ELEPHANT", 6 + k * 11, 20))
                attacks += attack_effects(tower, METHODS[tower], ref)
            for i in range(5):
                _add(s, 1, "VILLAGER_MALE", 8 + i * 2, 6)
            _add(s, 1, "TOWN_CENTER", 2, 2)
            _add(s, 2, "BARRACKS", 40, 21)
            blocks.anchor(ctx, player=2, at=(46, 46))
            ctx.trigger("Catapult towers", [], [
                *tower_effects(1), *attacks,
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": targets,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}])
            ctx.xs(xs_code(towers, targets))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 22, "initial_player_view_y": 16})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)


def report(record: Path) -> str:
    vals = list(struct.unpack_from(f"<{record.stat().st_size // 4}i", record.read_bytes()))
    if vals[0] != MAGIC:
        raise ValueError("not a crucible catapult tower record")
    n = vals[2]
    i = 3 + 2 * n
    lines = ["per tower: pierce / melee / vs buildings attack, target HP"]
    while i + 2 + 4 * n <= len(vals) and vals[i] == TAG_SAMPLE:
        t, row = vals[i + 1], vals[i + 2:i + 2 + 4 * n]
        lines.append(f"{t // 60}:{t % 60:02}  " + "   ".join(
            f"{TOWERS[k]} ({METHODS[TOWERS[k]]}) {row[4 * k]}/{row[4 * k + 1]}/{row[4 * k + 2]} hp {row[4 * k + 3]}"
            for k in range(n)))
        i += 2 + 4 * n
    return "\n".join(lines)
