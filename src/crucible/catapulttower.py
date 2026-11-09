"""A stuck-together catapult tower: towers that fire a Stone Thrower's stone with its damage.

A standalone scenario, `crucible_catapult_tower`, to look at. Every tower type player 1 owns (Watch, Sentry, Guard,
Ballista Tower) gets, for the whole type, so towers already placed and any you build:
- projectile: the catapult stone (656), arced;
- reload 5.4 s, range 10;
- splash width 0.8 at Blast Attack Level 6 (splash hits enemies only: the friendly fire fix);
- the arrow's pierce attack set to 0.

The Stone Thrower's attack (50 melee, +140 vs buildings) is the hard part. Round 2's log (2026-11-09): no trigger
method gives a tower an attack class it doesn't have (Modify Attribute Add or Set for the type, Modify Object
Attribute Add, Change Object Attack); the towers' melee and building attacks read −1 and each stone did 1 damage.
Triggers only change attack classes a unit already has. Round 3 tries the other routes, with the same log:

| Tower | Route |
|---|---|
| Watch | Trigger: set its existing pierce attack to 50 (pierce, not melee) |
| Sentry | XS `xsEffectAmount` Add (the path tech effects take): melee 50, +140 vs buildings |
| Guard | Data mod (Crucible Test Data): melee 50 and +140 vs buildings written into the Guard Tower |
| Ballista | XS `xsEffectAmount` Set: melee 50, +140 vs buildings |
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
METHODS = {"WATCH_TOWER": "pierce 50", "SENTRY_TOWER": "xs add", "GUARD_TOWER": "data mod",
           "BALLISTA_TOWER": "xs set"}
TOWER_IDS = {"WATCH_TOWER": 79, "SENTRY_TOWER": 234, "GUARD_TOWER": 235, "BALLISTA_TOWER": 236}
XS_SET, XS_ADD = 0, 4                  # xsEffectAmount effect types (cSetAttribute, cAddAttribute)
ATTACK, RELOAD, MAX_RANGE, SHOWN_RANGE, PROJECTILE_UNIT, BLAST_WIDTH, BLAST_LEVEL = 9, 10, 12, 47, 16, 22, 44
CATAPULT_STONE = 656
PIERCE, MELEE, BUILDINGS = 3, 4, 11                # attack classes
STONE_THROWER = {"melee": 50, "buildings": 140, "reload": 5.375, "range": 10, "blast": 0.8, "level": 6}
REVEAL_MAP, SET, ADD = 203, 1, 2
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412321111, 1, 1, 5

INSTRUCTIONS = """Crucible catapult tower, round 3. Pick "Crucible Test Data" as the Data Mod. Every tower you own \
fires a Stone Thrower's stone with its reload, range and splash (splash only hurts enemies). Each tower gets damage \
a different way, from the left: Watch (its pierce attack set to 50), Sentry (script, Add: 50 melee, +140 vs \
buildings), Guard (the data mod: 50 melee, +140 vs buildings), Ballista (script, Set). Which ones hit hard? Each \
tower's real attack values are logged. Enemies don't fight back. Nothing ends the game; a minute is enough."""


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


def attack_effects(tower: str, method: str, player: int = 1) -> list[dict]:
    """Trigger effects for the methods that use triggers (the XS and data mod ones are elsewhere)."""
    if method == "pierce 50":
        return [{"type": "modify_attribute", "source_player": player, "object_list_unit_id": tower,
                 "object_attributes": ATTACK, "operation": SET, "armour_attack_class": PIERCE,
                 "armour_attack_quantity": STONE_THROWER["melee"]}]
    return []


def xs_attack_code(player: int = 1) -> str:
    """xsEffectAmount calls for the XS methods. Attack values are encoded class * 256 + amount, as in tech effects."""
    calls = []
    for tower, method in METHODS.items():
        if method in ("xs add", "xs set"):
            kind = XS_ADD if method == "xs add" else XS_SET
            for cls, amount in ((MELEE, STONE_THROWER["melee"]), (BUILDINGS, STONE_THROWER["buildings"])):
                calls.append(f"    xsEffectAmount({kind}, {TOWER_IDS[tower]}, {ATTACK}, {cls * 256 + amount}, {player});")
    return "rule crucibleTowerAttack\n    active\n    highFrequency\n{\n" + "\n".join(calls) \
        + "\n    xsDisableSelf();\n}\n"


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
                attacks += attack_effects(tower, METHODS[tower])
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
            ctx.xs(xs_code(towers, targets) + "\n" + xs_attack_code(1))
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
