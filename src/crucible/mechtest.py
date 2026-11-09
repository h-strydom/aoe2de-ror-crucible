"""AoE2 mechanics in RoR, part 1: object attributes set by trigger (no data mod).

A standalone scenario, `crucible_mech_test`. Each lane puts a changed unit of yours (left) next to an unchanged copy
(further right), both set up the same way, so the difference is the attribute. Values follow AoE2's own where it
has them (docs/aoe2-mechanics.md). Short Swordsmen stand in for test bodies (the test data mod changes Hoplites).

| Lane | Test |
|---|---|
| 1 | **Regeneration** (109) 60 HP/min out of combat: a damaged swordsman and a damaged House |
| 2 | **Regeneration** in combat: a swordsman fighting an enemy swordsman |
| 3 | **Damage reflection** (118) 50%, melee: an enemy Axeman attacks your passive swordsman |
| 4 | **Damage reflection** 50%, ranged: an enemy Bowman shoots your passive swordsman |
| 5 | **Area damage** (115) 50% on a Bowman: with splash width 1, without, and a plain one |
| 6 | **Area damage** 50% on a swordsman: same three |
| 7 | **Bonus damage resistance** (24) 40% on Cavalry, attacked by Camel Riders (+8 vs cavalry) |
| 8 | **Add attack type** (161) "buildings", then +50 vs buildings, on an Axeman hitting a House; control: +50 only |
| 9 | **Dead unit** (57): a Horse Archer leaves a Bowman, a Camel Rider leaves a Broad Swordsman (killed at 0:15) |
| 10 | **Charge** (59-62) on War Elephants: type 1 (charged first hit, 30), type 3 (area charge), and a plain one |

A script logs hit points (and counts of Bowmen and Broad Swordsmen) every 2 seconds to
`<profile>/profile/crucible_mech_test.xsdat`; `crucible mech-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_mech_test"
SIZE = 80
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322001, 1, 1, 2
# Object attributes
REGEN, REFLECT, AREA, BONUS_RESIST, ADD_ATTACK, DEAD_UNIT = 109, 118, 115, 24, 161, 57
MAX_CHARGE, RECHARGE, CHARGE_EVENT, CHARGE_TYPE, BLAST_WIDTH, ATTACK = 59, 60, 61, 62, 22, 9
BUILDINGS_CLASS = 11
REVEAL_MAP, SET = 203, 1
LANE_Y = {k: 4 + (k - 1) * 7 for k in range(1, 11)}
X = (8, 34, 60)                                  # changed, second variant / control, control
BOWMAN, BROAD_SWORDSMAN = 4, 75

INSTRUCTIONS = """Crucible mechanics test, part 1 (triggers only). The map is revealed; nothing ends the game. \
Everything starts on its own: watch 2-3 minutes, then quit. In each lane the left unit is changed, the ones to its \
right are controls.

1 REGENERATION out of combat: left swordsman and House regenerate 60 HP/min after being damaged; do they heal?
2 REGENERATION in combat: the left swordsman regenerates while fighting an identical enemy. Does it win?
3 REFLECT melee: an enemy Axeman hits your passive swordsman, which reflects 50%. Does the Axeman lose HP?
4 REFLECT ranged: same with an enemy Bowman shooting. Does the Bowman lose HP?
5 AREA DAMAGE on a Bowman (50%): left also has splash width 1, middle has none, right is plain. Do neighbours \
of the target get hurt?
6 AREA DAMAGE on a swordsman: same three.
7 BONUS DAMAGE RESISTANCE 40% on the left Cavalry; Camel Riders attack both. Does the left one last longer?
8 ADD ATTACK TYPE: the left Axeman gains the 'buildings' attack class, then +50 vs buildings; the middle one only \
gets +50 vs buildings. Which House falls faster?
9 DEAD UNIT: at 0:15 the units die. Does the Horse Archer leave a Bowman and the Camel Rider a Broad Swordsman? \
Whose are they?
10 CHARGE on War Elephants: left type 1 (a charged first hit of 30), middle type 3 (area charge), right plain. \
Is there a charge bar? A bigger first hit? Splash?

Hit points are logged for the report."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(tracked: list[int]) -> str:
    """Every INTERVAL seconds: the count of player 1's Bowmen and Broad Swordsmen, then each tracked unit's HP."""
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(tracked), *tracked])
    hp = "".join(f"    crucibleMechHp({u});\n" for u in tracked)
    return f"""// ---- crucible mechanics test ----
void crucibleMechHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

rule crucibleMechInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleMechSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
    xsWriteInt(xsGetObjectCount(1, {BOWMAN}));
    xsWriteInt(xsGetObjectCount(1, {BROAD_SWORDSMAN}));
{hp}    xsCloseFile();
}}
"""


def build(out: Path) -> tuple[Path, list[tuple[str, int]]]:
    """Write the scenario; returns its path and the tracked units (label, reference id) in log order."""
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked: list[tuple[str, int]] = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            for p in (1, 2):
                fields = {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": p == 1,
                          "food": 0, "wood": 0, "gold": 0, "stone": 0, "population_cap": 200}
                if p == 2:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            settings, start, mine_passive, mine_stand, enemy_passive = [], [], [], [], []

            def attr(unit: int, attribute: int, value: float, player: int = 1) -> None:
                settings.append({"type": "modify_object_attribute", "source_player": player,
                                 "selected_object_ids": [unit], "object_attributes": attribute,
                                 "operation": SET, "quantity": value})

            def attack(who: list[int], target: int, player: int) -> None:
                start.append({"type": "task_object", "source_player": player, "selected_object_ids": who,
                              "location_object_reference": target})

            def track(label: str, unit: int) -> int:
                tracked.append((label, unit))
                return unit

            def clump(x: float, y: float) -> list[int]:
                ids = [_add(s, 2, "CLUBMAN", x + dx, y + dy) for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))]
                enemy_passive.extend(ids)
                return ids

            # 1 Regeneration out of combat: a swordsman and a House, damaged at the start.
            y = LANE_Y[1]
            for k, x in enumerate(X[:2]):
                sw = track(f"L1 swordsman {'regen' if k == 0 else 'control'}", _add(s, 1, "SHORT_SWORDSMAN", x, y))
                house = track(f"L1 House {'regen' if k == 0 else 'control'}", _add(s, 1, "HOUSE", x + 4, y))
                mine_stand.append(sw)
                settings += [{"type": "damage_object", "source_player": 1, "selected_object_ids": [sw, house],
                              "quantity": 40}]
                if k == 0:
                    attr(sw, REGEN, 60)
                    attr(house, REGEN, 60)

            # 2 Regeneration in combat.
            y = LANE_Y[2]
            for k, x in enumerate(X[:2]):
                me = track(f"L2 swordsman {'regen' if k == 0 else 'control'}", _add(s, 1, "SHORT_SWORDSMAN", x, y))
                foe = track(f"L2 enemy {'vs regen' if k == 0 else 'vs control'}",
                            _add(s, 2, "SHORT_SWORDSMAN", x + 1.5, y))
                if k == 0:
                    attr(me, REGEN, 60)
                attack([me], foe, 1)
                attack([foe], me, 2)

            # 3, 4 Damage reflection: melee, then ranged attackers on a passive swordsman.
            for lane, foe_unit, gap in ((3, "AXEMAN", 1.5), (4, "BOWMAN", 4)):
                y = LANE_Y[lane]
                for k, x in enumerate(X[:2]):
                    me = track(f"L{lane} swordsman {'reflect' if k == 0 else 'control'}",
                               _add(s, 1, "SHORT_SWORDSMAN", x, y))
                    foe = track(f"L{lane} attacker {'vs reflect' if k == 0 else 'vs control'}",
                                _add(s, 2, foe_unit, x + gap, y))
                    mine_passive.append(me)
                    if k == 0:
                        attr(me, REFLECT, 0.5)
                    attack([foe], me, 2)

            # 5, 6 Area damage on a ranged and a melee attacker: with splash width 1, without, and plain.
            for lane, unit, gap in ((5, "BOWMAN", 5), (6, "SHORT_SWORDSMAN", 1.5)):
                y = LANE_Y[lane]
                for k, x in enumerate(X):
                    me = _add(s, 1, unit, x, y)
                    ids = clump(x + gap + 1, y)
                    kind = ("area+splash", "area only", "plain")[k]
                    track(f"L{lane} {kind}: target", ids[0])
                    track(f"L{lane} {kind}: neighbour", ids[3])
                    if k < 2:
                        attr(me, AREA, 0.5)
                    if k == 0:
                        attr(me, BLAST_WIDTH, 1)
                    mine_stand.append(me)
                    attack([me], ids[0], 1)

            # 7 Bonus damage resistance: Camel Riders (+8 vs cavalry) attack two Cavalry.
            y = LANE_Y[7]
            for k, x in enumerate(X[:2]):
                me = track(f"L7 Cavalry {'resist 40%' if k == 0 else 'control'}", _add(s, 1, "CAVALRY", x, y))
                mine_passive.append(me)
                foes = [_add(s, 2, "CAMEL_RIDER", x + 2, y + d) for d in (-1, 1)]
                if k == 0:
                    attr(me, BONUS_RESIST, 0.4)
                attack(foes, me, 2)

            # 8 Add attack type: buildings class first, then +50 vs buildings; the control only gets the +50.
            y = LANE_Y[8]
            for k, x in enumerate(X[:2]):
                me = _add(s, 1, "AXEMAN", x, y)
                label = f"L8 House hit by {'added class' if k == 0 else 'set only'}"
                house = track(label, _add(s, 2, "HOUSE", x + 3, y))
                if k == 0:
                    attr(me, ADD_ATTACK, BUILDINGS_CLASS)
                # Attack goes in its own fields; an encoded class * 256 + amount in `quantity` writes a file the
                # parser can't read back.
                settings.append({"type": "modify_object_attribute", "source_player": 1, "selected_object_ids": [me],
                                 "object_attributes": ATTACK, "operation": SET,
                                 "armour_attack_class": BUILDINGS_CLASS, "armour_attack_quantity": 50})
                mine_stand.append(me)
                attack([me], house, 1)

            # 9 Dead unit: what a unit leaves when it dies.
            y = LANE_Y[9]
            ha = track("L9 Horse Archer (leaves Bowman)", _add(s, 1, "HORSE_ARCHER", X[0], y))
            camel = track("L9 Camel Rider (leaves Broad Swordsman)", _add(s, 1, "CAMEL_RIDER", X[0] + 6, y))
            plain = track("L9 Horse Archer control", _add(s, 1, "HORSE_ARCHER", X[1], y))
            mine_stand += [ha, camel, plain]
            attr(ha, DEAD_UNIT, BOWMAN)
            attr(camel, DEAD_UNIT, BROAD_SWORDSMAN)
            kill = {"type": "kill_object", "source_player": 1, "selected_object_ids": [ha, camel, plain]}

            # 10 Charge on War Elephants: type 1, type 3 (area, with splash width 1), plain.
            y = LANE_Y[10]
            for k, x in enumerate(X):
                me = _add(s, 1, "WAR_ELEPHANT", x, y)
                ids = clump(x + 3, y)
                kind = ("charge type 1", "charge type 3", "plain")[k]
                track(f"L10 {kind}: target", ids[0])
                track(f"L10 {kind}: neighbour", ids[3])
                if k == 0:
                    for a, v in ((MAX_CHARGE, 30), (RECHARGE, 0.5), (CHARGE_EVENT, 1), (CHARGE_TYPE, 1)):
                        attr(me, a, v)
                elif k == 1:
                    for a, v in ((MAX_CHARGE, 12), (RECHARGE, 0.5), (CHARGE_EVENT, 1), (CHARGE_TYPE, 3),
                                 (BLAST_WIDTH, 1)):
                        attr(me, a, v)
                mine_stand.append(me)
                attack([me], ids[0], 1)

            _add(s, 1, "TOWN_CENTER", 74, 74)
            blocks.anchor(ctx, player=2, at=(78, 2))
            stances = [{"type": "change_object_stance", "source_player": 1, "selected_object_ids": mine_passive,
                        "attack_stance": "NO_ATTACK_STANCE"},
                       {"type": "change_object_stance", "source_player": 1, "selected_object_ids": mine_stand,
                        "attack_stance": "STAND_GROUND"},
                       {"type": "change_object_stance", "source_player": 2, "selected_object_ids": enemy_passive,
                        "attack_stance": "NO_ATTACK_STANCE"},
                       {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                        "operation": "SET"}]
            ctx.trigger("Mechanics settings", [], [*stances, *settings])
            ctx.trigger("Start", [{"type": "timer", "timer": 3}], start)
            ctx.trigger("Kill lane 9", [{"type": "timer", "timer": 15}], [kill])
            ctx.xs(xs_code([u for _, u in tracked]))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 20, "initial_player_view_y": 20})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path, tracked
    finally:
        SESSIONS.close(o.handle)


def report(record: Path, labels: list[str]) -> str:
    vals = list(struct.unpack_from(f"<{record.stat().st_size // 4}i", record.read_bytes()))
    if vals[0] != MAGIC:
        raise ValueError("not a crucible mechanics test record")
    n = vals[2]
    i = 3 + n
    samples = []
    while i + 4 + n <= len(vals) and vals[i] == TAG_SAMPLE:
        samples.append((vals[i + 1], vals[i + 2], vals[i + 3], vals[i + 4:i + 4 + n]))
        i += 4 + n
    if not samples:
        return "no samples recorded"
    picks = [s for s in samples if s[0] in (0, 2, 4, 6, 10, 16, 20, 30, 45, 60, 90, 120, 180)] or samples
    head = "unit".ljust(44) + "".join(f"{t // 60}:{t % 60:02}".rjust(7) for t, *_ in picks)
    rows = [head]
    for k, label in enumerate(labels[:n]):
        rows.append(label[:43].ljust(44) + "".join(str(hp[k]).rjust(7) for *_, hp in picks))
    rows.append("your Bowmen".ljust(44) + "".join(str(b).rjust(7) for _, b, _, _ in picks))
    rows.append("your Broad Swordsmen".ljust(44) + "".join(str(b).rjust(7) for _, _, b, _ in picks))
    return "\n".join(rows)


def labels() -> list[str]:
    """The tracked units' labels, in log order (rebuilds the scenario in a temporary folder)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        return [label for label, _ in build(Path(tmp))[1]]
