"""Unit fire modes and economy tricks from AoE2, in RoR (`crucible_unit_test`, with the Crucible Test Data mod).

- **Chu Ko Nu** (trigger): a Bowman fires 3 arrows a shot (total and max total projectiles 3, secondary arrow
  510); a plain one beside it.
- **Kipchak** (data mod): Horse Archers fire 3 arrows spread over a 1 x 1 area.
- **Mangonel** (trigger): a Bowman fires a catapult stone with splash width 1 and blast level 2 at a clump.
- **Manual mode** (data mod): Bowmen can switch to a siege mode (stone, +40 vs buildings): trait 8 and the
  alternate unit, like the Ratha.
- **Automatic switch**: AoE2's Fire Archer and the Danes' Hearth Troop (ported whole) attack a House with a Clubman
  beside it; a RoR Bowman gets the Fire Archer's charge settings by trigger (type 6, target 191, a stone).
- **Khmer farmers** (trigger): player resource 33 ("Effect Function Number") set to 50, as AoE2's Khmer bonus does,
  with farms far from any drop site.
- **No drop-off, wood** (XS): a 1 s script moves what each lumberjack holds into the stockpile
  (`cUnitAttributeHeld`).
- **Mercenaries** (data mod): a Cavalry copy at the Town Center costs 1 of resource 214; a Wonder tech gives your
  team 5.

A script logs resources, mercenary tokens and tracked HP every 5 s to `<profile>/profile/crucible_unit_test.xsdat`;
`crucible unit-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import FIRE_ARCHER, HEARTH_TROOP, MERC_TOKEN, LUMBERJACKS, ported_ids, unit_mode_ids

NAME = "crucible_unit_test"
SIZE = 72
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322003, 1, 1, 5
REVEAL_MAP, SET = 203, 1
TOTAL_MISSILES, MAX_MISSILES, SECONDARY_PROJECTILE, CKN_ARROW = 102, 107, 65, 510
PROJECTILE, BLAST_WIDTH, BLAST_LEVEL, CATAPULT_SHOT = 16, 22, 44, 656
MAX_CHARGE, RECHARGE, CHARGE_EVENT, CHARGE_TYPE, CHARGE_PROJECTILE, CHARGE_TARGET = 59, 60, 61, 62, 125, 162
FIRE_ARCHER_CHARGE = ((MAX_CHARGE, 20), (RECHARGE, 0.5), (CHARGE_EVENT, -4), (CHARGE_TYPE, 6),
                      (CHARGE_PROJECTILE, CATAPULT_SHOT), (CHARGE_TARGET, 191))
EFFECT_FUNCTION, KHMER_FARMERS = 33, 50
LANE_Y = {k: 6 + (k - 1) * 8 for k in range(1, 6)}

INSTRUCTIONS = """Crucible unit test. Pick "Crucible Test Data" as the Data Mod. The map is revealed; nothing ends the \
game. Watch 3 minutes, then try the buttons.

1 CHU KO NU (top): the left Bowman should fire 3 arrows a shot; the right one is plain.
2 KIPCHAK: the Horse Archers should fire 3 arrows spread out.
3 MANGONEL: the left Bowman fires a catapult stone with splash at a clump; the right one is plain. Splash?
4 MANUAL MODE: select a Bowman: is there a button to switch to a siege mode (fires stones, +40 vs buildings)? \
Switch it and attack the enemy House.
5 AUTOMATIC SWITCH: AoE2's Fire Archer (left) and Hearth Troop (middle) attack a House; on the right a RoR Bowman \
given the Fire Archer's charge settings. Do they fire something special at the House (and normal arrows or blows at \
the Clubman beside it)?
KHMER FARMERS (bottom left): farmers work farms with no drop site nearby. Does food arrive without walking back?
NO DROP-OFF, WOOD (bottom middle): lumberjacks far from any drop site; a script banks what they carry. Wood rising?
MERCENARIES: the Town Center has a Mercenary Cavalry button that costs a token; you have none. Research the Wonder's \
last tech (your team gets 5 tokens), then train: can you train exactly 5?"""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(tracked: list[int], merc: int) -> str:
    """The wood no-drop-off rule, and the log: player 1's food, wood, gold, stone and mercenary tokens, player 3's
    tokens, player 1's Mercenary Cavalry count, then each tracked unit's HP."""
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(tracked), *tracked])
    hp = "".join(f"    crucibleUnitHp({u});\n" for u in tracked)
    bank = "".join(f"""    list = xsGetPlayerUnitIds(1, {jack});
    for (i = 0; < xsArrayGetSize(list)) {{
        id = xsArrayGetInt(list, i);
        held = xsGetUnitProperty(id, cUnitAttributeHeld);
        if (held > 0.0) {{
            xsSetPlayerAttribute(1, 1, xsPlayerAttribute(1, 1) + held);
            xsSetUnitProperty(id, cUnitAttributeHeld, 0.0);
        }}
    }}
""" for jack in LUMBERJACKS)
    return f"""// ---- crucible unit test ----
void crucibleUnitHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

rule crucibleUnitInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

// No drop-off for wood: whatever a lumberjack holds goes straight into the stockpile.
rule crucibleWoodNoDropOff
    active
    minInterval 1
{{
    int list = -1;
    int id = -1;
    float held = 0.0;
{bank}}}

rule crucibleUnitSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
    for (r = 0; < 4) {{
        xsWriteInt(xsPlayerAttribute(1, r));
    }}
    xsWriteInt(xsPlayerAttribute(1, {MERC_TOKEN}));
    xsWriteInt(xsPlayerAttribute(3, {MERC_TOKEN}));
    xsWriteInt(xsGetObjectCount(1, {merc}));
{hp}    xsCloseFile();
}}
"""


def build(out: Path) -> tuple[Path, list[tuple[str, int]]]:
    ids = ported_ids()
    _, merc = unit_mode_ids()
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked: list[tuple[str, int]] = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 3
            for p in (1, 2, 3):
                fields = {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": p == 1,
                          "food": 1000 if p == 1 else 0, "wood": 1000 if p == 1 else 0,
                          "gold": 1000 if p == 1 else 0, "stone": 1000 if p == 1 else 0, "population_cap": 200}
                if p > 1:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            diplomacy_set(o.handle, 1, [3], "ALLY")
            diplomacy_set(o.handle, 2, [3], "NEUTRAL")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            settings, start, stand, passive = [], [], [], []

            def attr(unit: int, attribute: int, value: float) -> None:
                settings.append({"type": "modify_object_attribute", "source_player": 1, "selected_object_ids": [unit],
                                 "object_attributes": attribute, "operation": SET, "quantity": value})

            def clump(x: float, y: float, label: str) -> list[int]:
                spots = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
                ids_ = [_add(s, 2, "CLUBMAN", x + dx, y + dy) for dx, dy in spots]
                passive.extend(ids_)
                tracked.extend(((f"{label}: target", ids_[0]), (f"{label}: neighbour", ids_[3])))
                return ids_

            def shooter(unit: str | int, x: float, y: float, target: int) -> int:
                me = _add(s, 1, unit, x, y)
                stand.append(me)
                start.append({"type": "task_object", "source_player": 1, "selected_object_ids": [me],
                              "location_object_reference": target})
                return me

            # 1 Chu Ko Nu, 3 Mangonel: a changed Bowman and a plain one, each against a clump.
            for lane, label in ((1, "Chu Ko Nu"), (3, "Mangonel")):
                y = LANE_Y[lane]
                for k, x in enumerate((8, 36)):
                    kind = label if k == 0 else f"plain ({label} lane)"
                    targets = clump(x + 6, y, kind)
                    me = shooter("BOWMAN", x, y, targets[0])
                    if k == 0 and lane == 1:
                        for a, v in ((TOTAL_MISSILES, 3), (MAX_MISSILES, 3), (SECONDARY_PROJECTILE, CKN_ARROW)):
                            attr(me, a, v)
                    elif k == 0:
                        for a, v in ((PROJECTILE, CATAPULT_SHOT), (BLAST_WIDTH, 1), (BLAST_LEVEL, 2)):
                            attr(me, a, v)

            # 2 Kipchak: Horse Archers (changed in the data mod) against a clump.
            y = LANE_Y[2]
            targets = clump(14, y, "Kipchak")
            for k in range(2):
                shooter("HORSE_ARCHER", 8, y - 1 + k * 2, targets[0])

            # 4 Manual mode: a Bowman (switchable in the data mod) by an enemy House and Clubmen.
            y = LANE_Y[4]
            stand.append(_add(s, 1, "BOWMAN", 8, y))
            tracked.append(("Manual mode: House", _add(s, 2, "HOUSE", 16, y)))
            passive += [_add(s, 2, "CLUBMAN", 14, y + 3)]

            # 5 Automatic switch: Fire Archer, Hearth Troop (ported), and a Bowman with the Fire Archer's charge.
            y = LANE_Y[5]
            for k, (unit, label) in enumerate(((ids[FIRE_ARCHER], "Fire Archer"), (ids[HEARTH_TROOP], "Hearth Troop"),
                                               ("BOWMAN", "Bowman with charge"))):
                x = 8 + k * 20
                house = _add(s, 2, "HOUSE", x + 6, y)
                tracked.append((f"{label}: House", house))
                club = _add(s, 2, "CLUBMAN", x + 4, y + 3)
                passive.append(club)
                tracked.append((f"{label}: Clubman", club))
                me = shooter(unit, x, y, house)
                if k == 2:
                    for a, v in FIRE_ARCHER_CHARGE:
                        attr(me, a, v)

            # Khmer farmers: farms with no drop site nearby (the Town Center is far right).
            farmers = []
            for k in range(4):
                farm = _add(s, 1, "FARM", 6 + k * 4, 54)
                farmers.append(_add(s, 1, "VILLAGER_MALE", 6 + k * 4, 58))
                start.append({"type": "task_object", "source_player": 1, "selected_object_ids": [farmers[-1]],
                              "location_object_reference": farm})
            settings.append({"type": "modify_resource", "tribute_list": EFFECT_FUNCTION, "source_player": 1,
                             "quantity": KHMER_FARMERS, "operation": "SET"})

            # No drop-off for wood: lumberjacks by a forest, no drop site nearby.
            trees = []
            for x in range(30, 38):
                for yy in range(56, 64):
                    if (x + yy) % 2 == 0:
                        trees.append(_add(s, 0, "TREE_A", x, yy))
            for k in range(4):
                jack = _add(s, 1, "VILLAGER_MALE", 28, 56 + k * 2)
                start.append({"type": "task_object", "source_player": 1, "selected_object_ids": [jack],
                              "location_object_reference": trees[k]})

            # Mercenaries: the Town Center trains them, the Wonder's last tech gives the tokens.
            _add(s, 1, "TOWN_CENTER", 64, 30)
            _add(s, 1, "WONDER", 52, 60)
            for k in range(8):
                _add(s, 1, "HOUSE", 56 + (k % 4) * 3, 8 + (k // 4) * 3)
            _add(s, 3, "TOWN_CENTER", 64, 50)
            blocks.anchor(ctx, player=2, at=(70, 70))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": passive,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "change_object_stance", "source_player": 1, "selected_object_ids": stand,
                 "attack_stance": "STAND_GROUND"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}, *settings])
            ctx.trigger("Start", [{"type": "timer", "timer": 3}], start)
            ctx.xs(xs_code([u for _, u in tracked], merc))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 24, "initial_player_view_y": 20})
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
        raise ValueError("not a crucible unit test record")
    n = vals[2]
    i, width = 3 + n, 2 + 4 + 3 + n
    samples = []
    while i + width <= len(vals) and vals[i] == TAG_SAMPLE:
        samples.append(vals[i + 1:i + width])
        i += width
    if not samples:
        return "no samples recorded"
    picks = [r for r in samples if r[0] in (5, 10, 20, 30, 45, 60, 90, 120, 180, 240, 300)] or samples
    rows = ["".ljust(32) + "".join(f"{r[0] // 60}:{r[0] % 60:02}".rjust(7) for r in picks)]
    for k, label in enumerate(("food", "wood", "gold", "stone", "your tokens", "ally tokens", "mercenaries")):
        rows.append(label.ljust(32) + "".join(str(r[1 + k]).rjust(7) for r in picks))
    for k, label in enumerate(names[:n]):
        rows.append(label[:31].ljust(32) + "".join(str(r[8 + k]).rjust(7) for r in picks))
    return "\n".join(rows)
