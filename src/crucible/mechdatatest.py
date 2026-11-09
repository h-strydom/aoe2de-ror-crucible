"""AoE2 mechanics in RoR, part 2: unit tasks and techs from the data mod.

A standalone scenario, `crucible_mech_data_test`, played with the Crucible Test Data mod picked. The data mod copies
AoE2 unit tasks onto RoR units, ports some AoE2 units whole and adds techs (testmod.py, `_mechanics`).

Round 1 (2026-11-09): HP transform, the Mule Cart and the Wonder techs (spawn, curse, team gift) work. The copied
auras (phalanx armour, a Town Center speed aura) and loot did nothing; extra spawn couldn't be tested (an Iron Age
start upgrades Clubmen).

Round 2 adds:
- **Whole ports**: the Camel Raider (loot) and the Centurion (aura on swordsman ids, which are swordsmen in RoR too);
  the Chronicles Hoplite's phalanx now names its own ported id. Do AoE2's own units' auras and loot work in RoR?
- **Extra spawn** on Axemen too.
- **Out-of-combat regeneration** (Mutalisk-style) by script: a 1 s rule switches a unit's regeneration off for 5 s
  whenever its HP drops (`xsEffectAmount(cSetUnitAttribute, unit, 109, ...)`), against a unit with plain
  regeneration (trigger) taking the same hits.
- **Half a pop slot**, four ways: RoR's own Logistics forced at 0:30 (attribute 110 = -0.5 on Slingers and other
  infantry); triggers setting 110 = -0.5 at 1:00, on Bowmen as AoE2ScenarioParser writes it (the parser lists 110
  as an integer attribute, so only the integer field is written, and it reads back as -1: likely the campaign's
  failure; aoe-editor refuses the fraction outright) and on Horse Archers with the float field forced to -0.5;
  XS `xsEffectAmount(cSetAttribute, Camel Rider, 110, -0.5)` at 1:30; Scouts made half-pop in the data (AoE2's
  Karambit storages). Ten of each are placed; train more to see the cost of new ones.

A script logs every 5 seconds to `<profile>/profile/crucible_mech_data_test.xsdat`; `crucible mech-data-report`
prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import (AXEMAN, CAMEL_RAIDER, CENTURION, CLUBMAN, LONG_SWORDSMAN, MULE_CART, SCOUT, SHORT_SWORDSMAN,
                      WAR_ELEPHANT, ported_ids)

NAME = "crucible_mech_data_test"
SIZE = 80
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322002, 2, 1, 5
REVEAL_MAP = 203
CHRONICLES_HOPLITE = 2110
SLINGER, BOWMAN, CAMEL_RIDER, HORSE_ARCHER = 7, 4, 329, 39
LOGISTICS, POP_COST = 121, 110
POP_HEADROOM, POPULATION = 4, 11                  # player attributes
REGEN, REGEN_RATE, REGEN_COOLDOWN, PULSE, PULSE_EVERY = 109, 60, 5, 20, 8
COUNTED = (CLUBMAN, AXEMAN, SHORT_SWORDSMAN, LONG_SWORDSMAN, WAR_ELEPHANT, SLINGER, BOWMAN, SCOUT, CAMEL_RIDER,
           HORSE_ARCHER)
COUNT_LABELS = ("clubmen", "axemen", "short-sw", "long-sw", "elephants", "slingers", "bowmen", "scouts", "camels",
                "horse-archers")
HALF_POP_XS_AT = 90

INSTRUCTIONS = """Crucible mechanics test, part 2, round 2. Pick "Crucible Test Data" as the Data Mod. The map is \
revealed; nothing ends the game. Run it 3-4 minutes.

AURAS AND LOOT, AoE2's own units ported whole: CAMEL RAIDERS (top) attack passive Clubmen: does your gold go up per \
kill? The CENTURION (left middle) stands by three Short Swordsmen; three more stand far right: are the near ones \
faster or quicker to attack? The ported Chronicles HOPLITES (top left, below the RoR ones) now point their phalanx at \
themselves: does the cluster's armour beat the lone one's?
EXTRA SPAWN: train an Axeman at the Barracks: do two come out?
OUT-OF-COMBAT REGEN (three Cavalry, right): the left two take 20 damage every 8 s. Left: regenerates only after 5 s \
without damage (script). Middle: plain regeneration. Right: damaged once, script regen. Watch their HP.
HALF POP: 10 each of Slingers, Bowmen, Scouts, Camel Riders (bottom). 0:30 Logistics is researched (Slingers and \
other infantry: half a slot); 1:00 a trigger makes Bowmen half a slot; 1:30 a script does Camel Riders; Scouts are \
half a slot in the data. Watch your population at each step, then train a few of each: does a new one cost half?
Round 1 items (Mule Cart, berserk, Wonder techs) are still here."""


def _float_effect_class():
    from AoE2ScenarioParser.objects.data_objects.effect import Effect

    class FloatQuantityEffect(Effect):
        """An effect whose quantity goes in the float field whatever the attribute: AoE2ScenarioParser writes only
        the integer field for attributes it lists as integers, such as 110 (population)."""

        @property
        def _quantity_int(self) -> int:
            return -1

        @property
        def _quantity_float(self):
            return self.quantity

    return FloatQuantityEffect


_FloatQuantityEffect = _float_effect_class()


def _add(s, player: int, unit: str | int, x: float, y: float, **kw) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5, **kw).reference_id


def xs_code(enemy_hoplite: int, regen: tuple[int, int], tracked: tuple[int, int, int]) -> str:
    """Logging, plus the out-of-combat regeneration rule for the `regen` units. Every INTERVAL seconds: player 1's
    food, wood, gold, stone; player 3's food; player 1's population headroom and population; counts of COUNTED; one
    enemy Hoplite's HP; the `tracked` Cavalry's HP."""
    counts = "".join(f"    xsWriteInt(xsGetObjectCount(1, {u}));\n" for u in COUNTED)
    hps = "".join(f"    crucibleHp({u});\n" for u in tracked)
    decls = "".join(f"int crucibleRegenLast{k} = -1;\nint crucibleRegenCool{k} = 0;\n" for k in range(len(regen)))
    regen_init = "".join(f"    xsEffectAmount(cSetUnitAttribute, {u}, {REGEN}, {REGEN_RATE}, 1);\n" for u in regen)
    # Round 2 crashed the game the moment the scripted Cavalry died (crash report WorldTime 1:20, its HP 0): don't
    # touch a unit at 0 HP (dying units still "exist").
    regen_body = "".join(f"""    hp = 0;
    if (xsDoesUnitExist({u})) {{
        hp = xsGetUnitHitpoints({u});
    }}
    if (hp > 0) {{
        if (hp < crucibleRegenLast{k}) {{
            if (crucibleRegenCool{k} == 0) {{
                xsEffectAmount(cSetUnitAttribute, {u}, {REGEN}, 0, 1);
            }}
            crucibleRegenCool{k} = {REGEN_COOLDOWN};
        }} else if (crucibleRegenCool{k} > 0) {{
            crucibleRegenCool{k} = crucibleRegenCool{k} - 1;
            if (crucibleRegenCool{k} == 0) {{
                xsEffectAmount(cSetUnitAttribute, {u}, {REGEN}, {REGEN_RATE}, 1);
            }}
        }}
        crucibleRegenLast{k} = hp;
    }}
""" for k, u in enumerate(regen))
    return f"""// ---- crucible mechanics test, part 2 ----
{decls}
void crucibleHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

rule crucibleMechDataInit
    active
    highFrequency
{{
    xsCreateFile(false);
    xsWriteInt({MAGIC});
    xsWriteInt({VERSION});
    xsCloseFile();
{regen_init}    xsDisableSelf();
}}

// Out-of-combat regeneration: a unit that lost HP since the last second stops regenerating for {REGEN_COOLDOWN} s.
rule crucibleOutOfCombatRegen
    active
    minInterval 1
{{
    int hp = 0;
{regen_body}}}

rule crucibleHalfPopCamels
    active
    minInterval 1
{{
    if (xsGetGameTime() >= {HALF_POP_XS_AT}) {{
        xsEffectAmount(cSetAttribute, {CAMEL_RIDER}, {POP_COST}, -0.5, 1);
        xsChatData("Script: Camel Riders set to half a pop slot", 0);
        xsDisableSelf();
    }}
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
    xsWriteInt(xsPlayerAttribute(1, {POP_HEADROOM}));
    xsWriteInt(xsPlayerAttribute(1, {POPULATION}));
{counts}    if (xsDoesUnitExist({enemy_hoplite})) {{
        hp = xsGetUnitHitpoints({enemy_hoplite});
    }}
    xsWriteInt(hp);
{hps}    xsCloseFile();
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
            passive, start, stand = [], [], []

            # Phalanx: clusters of five and lone ones, RoR Hoplites and the ported Chronicles Hoplites.
            for row, unit in ((6, "HOPLITE"), (14, ids[CHRONICLES_HOPLITE])):
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0.5, 2)):
                    _add(s, 1, unit, 6 + dx, row + dy)
                _add(s, 1, unit, 20, row)

            # Town Center aura (round 1, kept): Axemen beside the TC, and the same far away.
            _add(s, 1, "TOWN_CENTER", 6, 30)
            for k in range(3):
                _add(s, 1, "AXEMAN", 11, 28 + k * 2)
                _add(s, 1, "AXEMAN", 36, 28 + k * 2)

            # Loot: copied onto Axemen (round 1), and the ported Camel Raiders.
            for x, unit in ((34, "AXEMAN"), (52, ids[CAMEL_RAIDER])):
                looters = [_add(s, 1, unit, x, 4 + k * 2) for k in range(2)]
                victims = [_add(s, 2, "CLUBMAN", x + 4 + dx, 4 + dy) for dx in (0, 1.5) for dy in (0, 2, 4)]
                passive += victims
                start.append({"type": "task_object", "source_player": 1, "selected_object_ids": looters,
                              "location_object_reference": victims[0]})

            # Centurion (ported): three Short Swordsmen beside it, three far away.
            _add(s, 1, ids[CENTURION], 8, 42)
            for k in range(3):
                _add(s, 1, "SHORT_SWORDSMAN", 10, 40 + k * 2)
                _add(s, 1, "SHORT_SWORDSMAN", 40, 40 + k * 2)

            # HP transform: enemy Axemen attack two Short Swordsmen.
            swords = [_add(s, 1, "SHORT_SWORDSMAN", 34, 14 + k * 2) for k in range(2)]
            for k in range(3):
                a = _add(s, 2, "AXEMAN", 37, 13 + k * 2)
                start.append({"type": "task_object", "source_player": 2, "selected_object_ids": [a],
                              "location_object_reference": swords[k % 2]})

            # Curse target: passive enemy Hoplites.
            hoplites = [_add(s, 2, "HOPLITE", 28 + k * 1.5, 50) for k in range(3)]
            passive += hoplites

            # Out-of-combat regeneration: three Cavalry. The left two are hit every PULSE_EVERY seconds.
            scripted, plain, once = (_add(s, 1, "CAVALRY", x, 30) for x in (56, 62, 68))
            stand += [scripted, plain, once]
            regen_settings = [{"type": "modify_object_attribute", "source_player": 1, "selected_object_ids": [plain],
                               "object_attributes": REGEN, "operation": 1, "quantity": REGEN_RATE},
                              {"type": "damage_object", "source_player": 1, "selected_object_ids": [once],
                               "quantity": 80}]
            pulse = {"type": "damage_object", "source_player": 1, "selected_object_ids": [scripted, plain],
                     "quantity": PULSE}

            # Half a pop slot: ten Slingers, Bowmen and Scouts, and buildings to train more.
            for k in range(10):
                for row, unit in ((58, "SLINGER"), (61, "BOWMAN"), (64, "HORSE_ARCHER"), (67, "SCOUT"),
                                  (70, "CAMEL_RIDER")):
                    stand.append(_add(s, 1, unit, 40 + k * 1.5, row))
            _add(s, 1, "BARRACKS", 44, 44)
            _add(s, 1, "ARCHERY_RANGE", 60, 44)
            _add(s, 1, "STABLE", 70, 56)
            # Room to train (round 2: headroom was -66, since RoR's cap comes from Houses): Houses, plus 150 headroom.
            for k in range(15):
                _add(s, 1, "HOUSE", 20 + (k % 5) * 3, 70 + (k // 5) * 3)

            # Mule Cart: villagers by a forest far from the Town Center.
            for x in range(71, 78):
                for y in range(68, 78):
                    if (x + y) % 2 == 0:
                        _add(s, 0, "TREE_A", x, y)
            _add(s, 1, ids[MULE_CART], 67, 72)
            for k in range(4):
                _add(s, 1, "VILLAGER_MALE", 68, 69 + k * 2)

            # The Wonder, and the ally's base.
            _add(s, 1, "WONDER", 10, 64)
            _add(s, 3, "TOWN_CENTER", 74, 40)
            blocks.anchor(ctx, player=2, at=(78, 2))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": passive,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "change_object_stance", "source_player": 1, "selected_object_ids": stand,
                 "attack_stance": "STAND_GROUND"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"},
                {"type": "modify_resource", "tribute_list": POP_HEADROOM, "source_player": 1, "quantity": 150,
                 "operation": "ADD"}, *regen_settings])
            ctx.trigger("Start", [{"type": "timer", "timer": 3}], start)
            ctx.trigger("Regen pulse", [{"type": "timer", "timer": PULSE_EVERY}], [pulse], looping=True)
            ctx.trigger("Logistics", [{"type": "timer", "timer": 30}], [
                {"type": "research_technology", "source_player": 1, "technology": LOGISTICS,
                 "force_research_technology": 1}])
            # Written through the parser directly: aoe-editor rejects a fraction on attribute 110 (see the docstring).
            bowmen = s.trigger_manager.add_trigger("Half-pop Bowmen")
            bowmen.new_condition.timer(timer=60)
            bowmen.new_effect.modify_attribute(quantity=-0.5, object_list_unit_id=BOWMAN, source_player=1,
                                               operation=1, object_attributes=POP_COST)
            horse = bowmen.new_effect.modify_attribute(quantity=-0.5, object_list_unit_id=HORSE_ARCHER,
                                                       source_player=1, operation=1, object_attributes=POP_COST)
            horse.__class__ = _FloatQuantityEffect
            horse.quantity = -0.5                  # the parser already cut it to -1 when the effect was made
            ctx.xs(xs_code(hoplites[0], (scripted, once), (scripted, plain, once)))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 30, "initial_player_view_y": 30})
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
    if vals[1] < 2:
        raise ValueError("a round 1 record: rerun the round 2 scenario")
    width = 2 + 4 + 1 + 2 + len(COUNTED) + 1 + 3
    i = 2
    lines = ["time  food/wood/gold/stone  ally-food  headroom pop  " + " ".join(COUNT_LABELS)
             + "  enemy-hoplite  cav: scripted/plain/once"]
    while i + width <= len(vals) and vals[i] == TAG_SAMPLE:
        row = vals[i + 1:i + width]
        t, res, ally, room, pop = row[0], row[1:5], row[5], row[6], row[7]
        counts, hp, cav = row[8:8 + len(COUNTED)], row[8 + len(COUNTED)], row[9 + len(COUNTED):]
        lines.append(f"{t // 60}:{t % 60:02}  {'/'.join(map(str, res))}  {ally}  {room} {pop}  "
                     f"{' '.join(map(str, counts))}  {hp}  {'/'.join(map(str, cav))}")
        i += width
    return "\n".join(lines)
