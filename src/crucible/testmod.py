"""The data mod test: can a Crucible campaign depend on a mod for what triggers can't do?

Builds one local data mod and a two-mission test campaign:

- **Crucible Test Data**: Return of Rome's own data file and `dropsites.json`, with visible changes. (Hoplites had
  999 hit points and Axemen 400 for the first test; retired.) The Greek civilization loses its bonuses (Hoplites cost
  60 food 40 gold instead of 48/32), which tests "a civ with no bonuses". Houses accept wood. Pick it in the
  campaign's Data Mod dropdown.
- **crucible_mod_test**, the campaign: two identical missions (the second checks the data mod carries over). A
  trigger also makes Scouts trainable at the Barracks, testing "buildings that train units" with triggers alone.

First run (2026-11-09): a mod holding only `dropsites.json` under the data folder shows up in the Data Mod dropdown
as a data mod of its own, so drop sites and data changes must ship in one data mod. Clubmen were the wrong check:
starting in the Bronze Age researches Axe, which turns them into Axemen.

The data file is changed with genieutils-py, which writes RoR's file back identically when nothing is changed
(checked 2026-11-09: the decompressed bytes match; only the compression differs).
"""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.campaign import Campaign, CampaignScenario
from aoe2ed.config import find_game_dir
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

DATA_MOD, JSON_MOD, CAMPAIGN = "Crucible Test Data", "Crucible Test Dropsites", "crucible_mod_test"
ROR_DAT = Path("modes") / "Pompeii" / "resources" / "_common" / "dat"
# The first test gave Hoplites 999 HP and Axemen 400 (verified 2026-11-09). Retired the same day: later tests
# (mechanics) use those units and need their normal stats.
HP: dict[int, int] = {}
HOPLITE = 93
GREEK = 2                                  # civ index in RoR's data
HOUSE_IDS = [70, 463, 464, 465]            # the House and its age looks
STORAGE_PIT = 562
GRANARY = 68
LUMBERJACKS = (123, 218)                   # male and female lumberjack units (a villager's unit while chopping)
TRAIN_LOCATION, TRAIN_BUTTON, SET = 42, 43, 1
SCOUT_BUTTON = 9
MAX_MISSILES = 107                         # object attribute: Maximum Total Missiles (towers ship with 1)
GARRISON = 5                               # RoR towers' garrison capacity
SECONDARY_PROJECTILE, GARRISON_TYPE, GARRISON_FIREPOWER = 65, 30, 130      # object attributes
TOWER_ARROW_2 = 505                        # the secondary arrow AoE2's towers fire extra arrows with (in RoR's data)
VILLAGERS, INFANTRY = 1, 2                 # garrison type flags (RoR towers: 1, villagers only)
CIVILIAN, ARCHER = 4, 0                    # unit classes
VILLAGER = 83
GARRISON_ACTION, BUILDINGS, TRANSPORTS = 3, 3, 20     # task action type, and the classes a garrison task aims at
FOOT = (0, 6)                              # archer and infantry classes
FISHING_BOATS, GATHER_ACTION, FISH, WOOD = (13, 82), 5, 17, 1   # gather tasks name the resource they take
GUARD_TOWER, CATAPULT_ATTACKS = 235, ((4, 50), (11, 140))       # melee 50, +140 vs buildings (the Stone Thrower's)
BALLISTA_TOWER, CATAPULT_STONE = 236, 656
# Build slots on the villager's military page (interface kind 10; towers use 9). 14 and 15 didn't show (first try,
# 2026-11-09): AoE2's highest military slot is 13 (Castle). 10 is only used by the hero Zenobia's and Mirror
# Towers, 5 only by AoE2 buildings RoR doesn't have.
BALLISTA_BUTTON, CATAPULT_BUTTON = 10, 5
CATAPULT_TOWER_NAME = 7079                       # the string RoR's own "Catapult Tower" technology is named with
MONUMENT, RUINS = 826, 52                        # King of the Hill's Monument, Artifact Ruins
ARTIFACT, ARTIFACT_CLASS, PRIEST_CLASS, INFANTRY_CLASS = 25, 1, 18, 6
BARRACKS = (12, 20, 132, 498)                    # the Barracks and its age looks
EVERY_GARRISON = 127                             # garrison type: every category
AOE2_DAT = Path("resources") / "_common" / "dat"
# Ported from AoE2's data file: Knight (a slot RoR reuses for its Cavalry), Crossbowman (ranged: brings its
# projectiles), and the Chronicles Hoplite and Immortal. Trained at the Barracks on free buttons.
PORTED = {38: 5, 24: 8, 2110: 9, 2101: 10}       # AoE2 unit id: Barracks button
# RoR portraits for the ports (their AoE2 icon ids index RoR's set: the Knight showed a priest, Chronicles ones were
# black): Heavy Cavalry, Improved Bowman, Hoplite, Centurion; 2174 is the Immortal's ranged form.
PORTED_ICONS = {38: 13, 24: 7, 2110: 16, 2101: 50, 2174: 50, 2327: 57, 1790: 50, 1968: 7, 2705: 16}
PORTED_TRAIN_TIME = 10
# Mutually exclusive techs, Chronicles-style: each one's effect disables all three. Names use Chronicles'
# Oligarchy / Democracy / Tyranny strings (does RoR have them?); each pays a different resource so the pick shows.
EXCLUSIVE = ((407051, 3, 11), (407052, 1, 12), (407053, 0, 13))   # name string, resource paid, Barracks button
EXCLUSIVE_PAY, EXCLUSIVE_COST, EXCLUSIVE_TIME = 200, 50, 20
# Costs are paid at queue time, so two could be queued and both researched (rounds 1-3; a cost in a spare resource is
# ignored, and a script disabling the others didn't hold). But in Chronicles, hovering one draws a red cross over the
# other and the other can't be started while one researches. The tech `type` is the suspect: Chronicles' unique techs
# are 0, the first sets were 9 (copied from RoR's Axe). 33 is the type of switchable settings (the Market's trade
# settings, the Athenian governments). Round 4 compares type 0 (Barracks) with type 33 (Town Center).
EXCLUSIVE_TYPE = 0
EXCLUSIVE_33 = ((407051, 2, 8), (407052, 3, 9))   # a type 33 pair at the Town Center: pays stone, gold
TOWN_CENTER = 109
# A tech at the Wonder: RoR's Wonder (276) has the Town Center's panel kind but no buttons at all. Named with the
# Wonder's own name string; pays 500 of each resource so it shows.
WONDER, WONDER_BUTTON, WONDER_PAY, WONDER_TIME = 276, 1, 500, 10
# AoE2 mechanics, part 2 (data only; docs/aoe2-mechanics.md). Unit tasks copied from AoE2 units onto RoR ones:
MULE_CART, MULE_BUTTON = 1808, 4                 # AoE2's Mule Cart (movable drop site), trained at the Town Center
CAMEL_RAIDER, JIAN, BLACKWOOD, CENTURION = 2327, 1974, 2579, 1790   # loot, HP transform, extra spawn, aura templates
# Round 2: the copied aura and loot tasks did nothing on RoR units. Port the AoE2 units whole to tell "copied wrong"
# from "RoR doesn't run these tasks": the Camel Raider (loot) and the Centurion, whose aura targets swordsman ids
# 74/75/77/473, which are swordsmen in RoR too. Placed in the scenario, not trained.
# Automatic attack switch (unit test): AoE2's Fire Archer (target-dependent fire projectile, charge type 6) and
# the Danes' Hearth Troop (throws its charge projectile).
FIRE_ARCHER, HEARTH_TROOP = 1968, 2705
PORTED_WHOLE = (CAMEL_RAIDER, CENTURION, FIRE_ARCHER, HEARTH_TROOP)
# Half a pop slot, the data way: AoE2's Karambit stores -0.5 population headroom (4), 0.5 population (11) and 0.5
# of resource 19 where a normal unit has -1, 1, 1. Applied to the Scout. (RoR's own Logistics sets attribute 110 to
# -0.5 instead; the scenario tests that and a trigger route.)
SCOUT, HALF_POP_STORAGES = 448, {4: -0.5, 11: 0.5, 19: 0.5}
# Unit fire modes (unit test): AoE2's Kipchak fires 3 arrows (total and max total projectiles 3, the Chu Ko Nu's
# secondary arrow 510) spread over a spawn area of 1 x 1; given to RoR's Horse Archer. Two fire modes, the Ratha's and
# the Immortal's way: trait 8 plus the alternate unit in `nothing`, both ways; the Bowman's other mode is a copy
# firing a catapult stone with +40 vs buildings. Limited training, Cuman Mercenaries' way: a unit costing 1 of
# resource 214 ("Mercenary Kipchak Count"), and a Wonder tech giving your team 5 of it.
HORSE_ARCHER, BOWMAN, CAVALRY = 39, 4, 38
KIPCHAK_SPREAD, KIPCHAK_ARROWS, CKN_ARROW = (1.0, 1.0, 1.0), 3, 510
SWITCH_TRAIT, CATAPULT_SHOT, SIEGE_BONUS, BUILDING_ARMOUR = 8, 656, 40, 11   # 11: the buildings armour class
MERC_TOKEN, MERC_BUTTON, MERC_GIFT, MERC_TECH_BUTTON = 214, 5, 5, 5
HOPLITE, AXEMAN, SHORT_SWORDSMAN, LONG_SWORDSMAN, CLUBMAN, WAR_ELEPHANT = 93, 531, 74, 77, 281, 1132
AURA, LOOT, HP_TRANSFORM, EXTRA_SPAWN = 155, 154, 158, 156
PHALANX = (116, 117)                             # the Chronicles Hoplite's per-hoplite aura stats (armour)
PHALANX_PER, PHALANX_MAX, PHALANX_RANGE = 2.0, 8.0, 3.0
TC_AURA_SPEED, TC_AURA_RANGE, INFANTRY = 1.5, 10.0, 6
TRANSFORM_AT = -50.0                             # below 50% HP (AoE2's Jian: -45)
# Three more Wonder techs (buttons 2-4): spawn 3 War Elephants at the Town Center (effect 7); a curse, enemy infantry
# HP x0.5 (effect 25: an attribute multiply on enemies); a team gift, +500 food for your team (effect 11).
WONDER_EXTRA = (("spawn", 2), ("curse", 3), ("team", 4))
SPAWN_UNIT, SPAWN_COUNT, CURSE_FACTOR, TEAM_GIFT = WAR_ELEPHANT, 3, 0.5, 500
AXE_TECH, DISABLE_TECH, RESOURCE_MODIFY = 63, 102, 1
SIZE = 48

INSTRUCTIONS = """Crucible mod test.

Before starting: in Mods > Installed Mods, enable "Crucible Test Data" (and disable "Crucible Test Dropsites" if \
it's still there), restart the game, then on the campaign screen set Data Mod to "Crucible Test Data".

1. HIT POINTS: (retired: Hoplites and Axemen now have their normal 120 and 50.)
2. GREEK BONUS GONE: train a Hoplite at the Academy. With the data mod: 60 food, 40 gold. With the normal Greek \
bonus: 48 food, 32 gold.
3. DROP SITE: send a villager to chop the trees beside the houses. Does it drop the wood at a House?
4. SCOUT AT BARRACKS (triggers only): does the Barracks offer a Scout?

Walk any unit onto the flag in the far corner to finish the mission. Mission 2 is the same: check 1 and 2 again \
to see that the data mod carried over."""


def _source_dat() -> Path:
    game = find_game_dir()
    if game is None:
        raise FileNotFoundError("AoE2 DE not found")
    return game / ROR_DAT


def build_data_mod(root: Path) -> Path:
    """The data mod folder: RoR's data file (tougher Hoplites and Axemen, Greeks without bonuses) and its
    dropsites.json (Houses take wood)."""
    from genieutils.datfile import DatFile
    d = DatFile.parse(str(_source_dat() / "empires2_x2_p1.dat"))
    for civ in d.civs:
        for uid, hp in HP.items():
            if len(civ.units) > uid and civ.units[uid]:
                civ.units[uid].hit_points = hp
        # A drop site needs both halves: dropsites.json makes the building accept the resource, and each villager job
        # unit lists the buildings it may drop at (second run, 2026-11-09: Houses showed the drop-off cursor but
        # lumberjacks went idle, because they only listed the Town Center and Storage Pit).
        for uid in LUMBERJACKS:
            unit = civ.units[uid] if len(civ.units) > uid else None
            if unit and unit.bird and HOUSE_IDS[0] not in unit.bird.drop_sites:
                unit.bird.drop_sites.append(HOUSE_IDS[0])
        _garrison_into_buildings(civ)
        _catapult_attack(civ)
        # Resource test: fishing boats told to take wood (not fish) from fish. Does a mismatched gather do anything?
        for uid in FISHING_BOATS:
            unit = civ.units[uid] if len(civ.units) > uid else None
            for t in (unit.bird.tasks if unit and unit.bird else []):
                if t.action_type == GATHER_ACTION and t.resource_in == FISH:
                    t.resource_in = WOOD
    _buildable_towers(d)
    _ruin_monument(d)
    _garrisonable_artifacts(d)
    aoe2 = _aoe2_dat()
    _ported_units(d, aoe2)
    _exclusive_techs(d)
    _wonder_tech(d)
    _mechanics(d, aoe2)
    mule = ported_ids()[MULE_CART]
    for civ in d.civs:                       # every villager job unit may drop at the Mule Cart
        for unit in civ.units:
            sites = unit.bird.drop_sites if unit and unit.class_ == CIVILIAN and unit.bird else None
            if sites and mule not in sites:
                sites.append(mule)
    _unit_modes(d)
    greek = d.civs[GREEK]
    tree = d.effects[greek.tech_tree_id]
    tree.effect_commands = [c for c in tree.effect_commands if c.type == 102]   # keep its disabled techs only
    for t in d.techs:
        if t.civ == GREEK and t.effect_id >= 0:
            d.effects[t.effect_id].effect_commands = []
    folder = root / DATA_MOD
    out = folder / ROR_DAT / "empires2_x2_p1.dat"
    out.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(out))
    data = json.loads((_source_dat() / "dropsites.json").read_text(encoding="utf-8"))
    pit = next(e for e in data["drop_site_list"] if e["building_id"] == STORAGE_PIT)
    trees = [t for t in pit["target_list"] if t["name"] == "Trees"]
    for hid in HOUSE_IDS:
        data["drop_site_list"].append({"name": "House", "building_id": hid,
                                       "worker_object_group": pit["worker_object_group"], "target_list": trees})
    _mule_cart_drop_site(data)
    (out.parent / "dropsites.json").write_text(json.dumps(data, indent=4), encoding="utf-8")
    _info(folder, DATA_MOD, "Crucible test: Greeks without bonuses, Houses take "
                            "wood (Return of Rome).")
    return folder


def _garrison_into_buildings(civ) -> int:
    """Give foot soldiers (archers, infantry) the villager's "garrison into a building" task. RoR's soldiers can only
    board transport ships; AoE2's also garrison in buildings (data compared, 2026-11-09). Returns units changed."""
    villager = civ.units[VILLAGER]
    if not (villager and villager.bird):
        return 0
    task = next((t for t in villager.bird.tasks if t.action_type == GARRISON_ACTION and t.class_id == BUILDINGS), None)
    if task is None:
        return 0
    changed = 0
    for unit in civ.units:
        if not (unit and unit.type == 70 and unit.class_ in FOOT and unit.bird):
            continue
        actions = {(t.action_type, t.class_id) for t in unit.bird.tasks}
        if (GARRISON_ACTION, TRANSPORTS) in actions and (GARRISON_ACTION, BUILDINGS) not in actions:
            new = copy.deepcopy(task)
            new.id = len(unit.bird.tasks)
            unit.bird.tasks.append(new)
            changed += 1
    return changed


def _catapult_attack(civ) -> bool:
    """Catapult tower test: give the Guard Tower the Stone Thrower's attack classes (50 melee, +140 vs buildings),
    which triggers can't add (round 2, 2026-11-09)."""
    tower = civ.units[GUARD_TOWER] if len(civ.units) > GUARD_TOWER else None
    if not (tower and tower.type_50 and tower.type_50.attacks):
        return False
    have = {a.class_ for a in tower.type_50.attacks}
    for cls, amount in CATAPULT_ATTACKS:
        if cls not in have:
            new = copy.deepcopy(tower.type_50.attacks[0])
            new.class_, new.amount = cls, amount
            tower.type_50.attacks.append(new)
    return True


def _buildable_towers(d) -> int:
    """Two more towers in the villager's build menu: the Ballista Tower as a building of its own (RoR only reaches
    it by upgrading the other towers) and a new Catapult Tower, a copy of the Guard Tower that fires the Stone
    Thrower's stone with its attack. Returns the new tower's unit id."""
    new_id = len(d.civs[0].units)
    for civ in d.civs:
        guard = civ.units[GUARD_TOWER] if len(civ.units) > GUARD_TOWER else None
        ballista = civ.units[BALLISTA_TOWER] if len(civ.units) > BALLISTA_TOWER else None
        if ballista and ballista.creatable:
            ballista.enabled = 1
            for t in ballista.creatable.train_locations:
                t.button_id = BALLISTA_BUTTON
        if not (guard and guard.type_50 and guard.creatable):
            civ.units.append(None)
            continue
        tower = copy.deepcopy(guard)
        tower.id = tower.copy_id = tower.base_id = new_id
        tower.enabled = 1
        tower.name = "Catapult Tower"
        tower.language_dll_name = CATAPULT_TOWER_NAME
        t50 = tower.type_50
        t50.projectile_unit_id = CATAPULT_STONE
        t50.reload_time = 5.375
        t50.max_range = t50.displayed_range = 10
        t50.min_range = 3
        t50.blast_width = 0.8
        t50.blast_attack_level = 6                     # splash hits enemies only
        template = t50.attacks[0]
        t50.attacks = []
        for cls, amount in CATAPULT_ATTACKS:
            a = copy.deepcopy(template)
            a.class_, a.amount = cls, amount
            t50.attacks.append(a)
        for t in tower.creatable.train_locations:
            t.button_id = CATAPULT_BUTTON
        civ.units.append(tower)
    return new_id


def ruin_monument_id() -> int:
    """The unit id the data mod gives the ruin-looking Monument (added right after the Catapult Tower)."""
    from genieutils.datfile import DatFile
    return len(DatFile.parse(str(_source_dat() / "empires2_x2_p1.dat")).civs[0].units) + 1


def _ruin_monument(d) -> int:
    """A copy of King of the Hill's Monument dressed as Artifact Ruins (graphic, icon, name, size). The KotH monument
    trickle pays for the Monument but not for ruins (ruins test, 2026-11-09), so a ruin that is really a Monument
    should trickle. Returns its unit id."""
    new_id = len(d.civs[0].units)
    for civ in d.civs:
        monument = civ.units[MONUMENT] if len(civ.units) > MONUMENT else None
        ruins = civ.units[RUINS] if len(civ.units) > RUINS else None
        if not (monument and ruins):
            civ.units.append(None)
            continue
        unit = copy.deepcopy(monument)
        unit.id = unit.copy_id = unit.base_id = new_id
        unit.name = "Ruin Monument"
        unit.standing_graphic = tuple(ruins.standing_graphic)
        unit.icon_id = ruins.icon_id
        unit.language_dll_name = ruins.language_dll_name
        unit.collision_size_x = unit.collision_size_y = ruins.collision_size_x
        unit.outline_size_x = unit.outline_size_y = ruins.outline_size_x
        civ.units.append(unit)
    return new_id


def artifact_ids() -> tuple[int, int]:
    """The unit ids the data mod gives its two artifact copies: (infantry class, priest class)."""
    first = ruin_monument_id() + 1
    return first, first + 1


def _garrisonable_artifacts(d) -> tuple[int, int]:
    """Can an artifact garrison? Artifacts are their own class (1), which no garrison type admits: a Relic Cart with
    a garrison task stayed out of a Barracks open to every category (ruins test, 2026-11-09). Three tries, side by
    side: the AoE1 artifact (25) gets the villager's "garrison into a building" task and keeps its class; two copies
    get the task too, one in the infantry class and one in the priest class. Every Barracks admits every category.
    Returns the copies' ids."""
    new_id = len(d.civs[0].units)
    for civ in d.civs:
        for uid in BARRACKS:
            if len(civ.units) > uid and civ.units[uid] and civ.units[uid].building:
                civ.units[uid].building.garrison_type = EVERY_GARRISON
        villager, artifact = civ.units[VILLAGER], civ.units[ARTIFACT] if len(civ.units) > ARTIFACT else None
        task = next((t for t in villager.bird.tasks if t.action_type == GARRISON_ACTION and t.class_id == BUILDINGS),
                    None) if villager and villager.bird else None
        if not (artifact and artifact.bird and task):
            civ.units += [None, None]
            continue
        if (GARRISON_ACTION, BUILDINGS) not in {(t.action_type, t.class_id) for t in artifact.bird.tasks}:
            new = copy.deepcopy(task)
            new.id = len(artifact.bird.tasks)
            artifact.bird.tasks.append(new)
        for k, (cls, name) in enumerate(((INFANTRY_CLASS, "Artifact (infantry class)"),
                                         (PRIEST_CLASS, "Artifact (priest class)"))):
            unit = copy.deepcopy(artifact)
            unit.id = unit.copy_id = unit.base_id = new_id + k
            unit.name, unit.class_ = name, cls
            civ.units.append(unit)
    return new_id, new_id + 1


def _aoe2_dat():
    from genieutils.datfile import DatFile
    return DatFile.parse(str(find_game_dir() / AOE2_DAT / "empires2_x2_p1.dat"))


def _ported_units(d, src=None) -> dict[int, int]:
    """Port the PORTED units (and everything they link to) from AoE2's data file, enable them and put them on the
    Barracks. Returns {AoE2 id: RoR id} for every unit ported."""
    from .port import Porter
    porter = Porter(src or _aoe2_dat(), d)
    for uid, (location, button) in [*((u, (BARRACKS[0], b)) for u, b in PORTED.items()),
                                    (MULE_CART, (TOWN_CENTER, MULE_BUTTON)),
                                    *((u, (None, None)) for u in PORTED_WHOLE)]:
        new = porter.unit(uid)
        for src_id, icon in PORTED_ICONS.items():
            if src_id in porter.units:
                for civ in d.civs:
                    if civ.units[porter.units[src_id]]:
                        civ.units[porter.units[src_id]].icon_id = icon
        for civ in d.civs:
            unit = civ.units[new]
            if unit is None:
                continue
            unit.enabled = 1
            if unit.creatable and location is not None:
                loc = unit.creatable.train_locations
                loc[0].unit_id, loc[0].button_id, loc[0].train_time = location, button, PORTED_TRAIN_TIME
                unit.creatable.train_locations = loc[:1]
    return dict(porter.units)


_PORTED_IDS: dict[int, int] | None = None


def ported_ids() -> dict[int, int]:
    """{AoE2 id: RoR id} as the data mod numbers them: rebuilds the ports on RoR's data padded to where they start
    (after the artifact copies). Slow (both data files are parsed), so cached."""
    global _PORTED_IDS
    if _PORTED_IDS is None:
        from genieutils.datfile import DatFile
        d = DatFile.parse(str(_source_dat() / "empires2_x2_p1.dat"))
        start = artifact_ids()[1] + 1
        for civ in d.civs:
            civ.units += [None] * (start - len(civ.units))
        _PORTED_IDS = _ported_units(d)
    return _PORTED_IDS


def exclusive_tech_ids() -> tuple[int, ...]:
    """Every exclusive tech the data mod adds: the EXCLUSIVE set, then the EXCLUSIVE_33 set."""
    from genieutils.datfile import DatFile
    first = len(DatFile.parse(str(_source_dat() / "empires2_x2_p1.dat")).techs)
    return tuple(range(first, first + len(EXCLUSIVE) + len(EXCLUSIVE_33)))


def _exclusive_techs(d) -> tuple[int, ...]:
    """Mutually exclusive tech sets (Chronicles' pattern: each choice's effect has a "disable tech" command for every
    tech in the set, itself included): EXCLUSIVE at the Barracks with type 0, EXCLUSIVE_33 at the Town Center with
    type 33. Returns all their ids."""
    return (_exclusive_set(d, EXCLUSIVE, BARRACKS[0], EXCLUSIVE_TYPE, "Crucible exclusive")
            + _exclusive_set(d, EXCLUSIVE_33, TOWN_CENTER, 33, "Crucible exclusive type 33"))


def _exclusive_set(d, spec, location: int, tech_type: int, label: str) -> tuple[int, ...]:
    first = len(d.techs)
    ids = tuple(range(first, first + len(spec)))
    template = d.techs[AXE_TECH]
    disable = next(c for e in d.effects for c in e.effect_commands if c.type == DISABLE_TECH)
    for k, (name, resource, button) in enumerate(spec):
        effect = copy.deepcopy(d.effects[template.effect_id])
        pay = copy.deepcopy(disable)
        pay.type, pay.a, pay.b, pay.c, pay.d = RESOURCE_MODIFY, resource, 1, -1, float(EXCLUSIVE_PAY)
        commands = [pay]
        for tid in ids:
            c = copy.deepcopy(disable)
            c.d = float(tid)
            commands.append(c)
        effect.effect_commands = commands
        effect.name = f"{label} {k + 1}"
        d.effects.append(effect)
        tech = copy.deepcopy(template)
        tech.name, tech.type = f"{label} {k + 1}", tech_type
        tech.language_dll_name, tech.language_dll_description = name, name + 1000
        tech.language_dll_help, tech.language_dll_tech_tree = name + 100000, name + 150000
        tech.effect_id, tech.civ, tech.repeatable = len(d.effects) - 1, -1, 0
        tech.required_techs, tech.required_tech_count = (-1,) * 6, 0
        costs = list(tech.resource_costs)
        costs[0].type, costs[0].amount, costs[0].flag = 0, EXCLUSIVE_COST, 1
        for c in costs[1:]:
            c.type, c.amount, c.flag = -1, 0, 0
        tech.resource_costs = tuple(costs)
        loc = tech.research_locations
        loc[0].location_id, loc[0].button_id, loc[0].research_time = location, button, EXCLUSIVE_TIME
        tech.research_locations = loc[:1]
        d.techs.append(tech)
    return ids


def wonder_tech_id() -> int:
    """The Wonder tech's id: added right after the exclusive techs."""
    return exclusive_tech_ids()[-1] + 1


def _wonder_tech(d) -> int:
    """A free tech researched at the Wonder, paying WONDER_PAY of food, wood, gold and stone. Returns its id."""
    template = d.techs[AXE_TECH]
    command = next(c for e in d.effects for c in e.effect_commands if c.type == DISABLE_TECH)
    effect = copy.deepcopy(d.effects[template.effect_id])
    pays = []
    for resource in (0, 1, 2, 3):
        c = copy.deepcopy(command)
        c.type, c.a, c.b, c.c, c.d = RESOURCE_MODIFY, resource, 1, -1, float(WONDER_PAY)
        pays.append(c)
    effect.effect_commands, effect.name = pays, "Crucible Wonder tech"
    d.effects.append(effect)
    tech = copy.deepcopy(template)
    name = d.civs[1].units[WONDER].language_dll_name
    tech.name, tech.type, tech.civ, tech.repeatable = "Crucible Wonder tech", 0, -1, 0
    tech.language_dll_name = name
    tech.effect_id = len(d.effects) - 1
    tech.required_techs, tech.required_tech_count = (-1,) * 6, 0
    for c in tech.resource_costs:
        c.type, c.amount, c.flag = -1, 0, 0
    loc = tech.research_locations
    loc[0].location_id, loc[0].button_id, loc[0].research_time = WONDER, WONDER_BUTTON, WONDER_TIME
    tech.research_locations = loc[:1]
    d.techs.append(tech)
    return len(d.techs) - 1


def wonder_extra_tech_ids() -> tuple[int, ...]:
    """The spawn, curse and team Wonder techs, added right after the first Wonder tech."""
    first = wonder_tech_id() + 1
    return tuple(range(first, first + len(WONDER_EXTRA)))


def _copy_tasks(unit, tasks, **changes) -> None:
    """Append copies of `tasks` to `unit`, with `changes` applied to each."""
    for t in tasks:
        new = copy.deepcopy(t)
        for k, v in changes.items():
            setattr(new, k, v)
        new.id = len(unit.bird.tasks)
        unit.bird.tasks.append(new)


def _mechanics(d, src) -> None:
    """AoE2 unit tasks on RoR units, and three more Wonder techs (mechanics test, part 2)."""
    s0 = src.civs[0].units
    phalanx = [next(t for t in s0[2110].bird.tasks if t.action_type == AURA and t.search_wait_time == stat)
               for stat in PHALANX]
    speed = next(t for t in s0[CENTURION].bird.tasks if t.action_type == AURA and t.search_wait_time == 5)
    loot = [t for t in s0[CAMEL_RAIDER].bird.tasks if t.action_type == LOOT]
    transform = [t for t in s0[JIAN].bird.tasks if t.action_type == HP_TRANSFORM]
    spawn = [t for t in s0[BLACKWOOD].bird.tasks if t.action_type == EXTRA_SPAWN]
    for civ in d.civs:
        u = civ.units
        if u[HOPLITE] and u[HOPLITE].bird:      # armour per nearby RoR Hoplite (the Chronicles phalanx)
            _copy_tasks(u[HOPLITE], phalanx, unit_id=HOPLITE, class_id=-1, work_value_1=PHALANX_PER,
                        work_value_2=PHALANX_MAX, work_range=PHALANX_RANGE)
        if u[TOWN_CENTER] and u[TOWN_CENTER].bird:   # a building aura: infantry nearby move faster
            _copy_tasks(u[TOWN_CENTER], [speed], unit_id=-1, class_id=INFANTRY, work_value_1=TC_AURA_SPEED,
                        work_range=TC_AURA_RANGE)
        if u[AXEMAN] and u[AXEMAN].bird:
            _copy_tasks(u[AXEMAN], loot)
        if u[SHORT_SWORDSMAN] and u[SHORT_SWORDSMAN].bird:
            _copy_tasks(u[SHORT_SWORDSMAN], transform, work_value_1=float(LONG_SWORDSMAN), work_value_2=TRANSFORM_AT)
        for uid in (CLUBMAN, AXEMAN):            # an Iron Age start upgrades Clubmen to Axemen (round 1)
            if u[uid] and u[uid].bird:
                _copy_tasks(u[uid], spawn, work_value_1=float(uid), work_value_2=1.0)
    for civ in d.civs:
        scout = civ.units[SCOUT] if len(civ.units) > SCOUT else None
        for storage in (scout.resource_storages if scout else []):
            if storage.type in HALF_POP_STORAGES:
                storage.amount = HALF_POP_STORAGES[storage.type]
    template = d.techs[AXE_TECH]
    command = next(c for e in d.effects for c in e.effect_commands if c.type == DISABLE_TECH)
    name = d.civs[1].units[WONDER].language_dll_name
    for label, button in WONDER_EXTRA:
        c = copy.deepcopy(command)
        if label == "spawn":
            c.type, c.a, c.b, c.c, c.d = 7, SPAWN_UNIT, TOWN_CENTER, SPAWN_COUNT, 0.0
        elif label == "curse":
            c.type, c.a, c.b, c.c, c.d = 25, -1, INFANTRY, 0, CURSE_FACTOR
        else:
            c.type, c.a, c.b, c.c, c.d = 11, 0, 1, -1, float(TEAM_GIFT)
        effect = copy.deepcopy(d.effects[template.effect_id])
        effect.effect_commands, effect.name = [c], f"Crucible Wonder {label}"
        d.effects.append(effect)
        tech = copy.deepcopy(template)
        tech.name, tech.type, tech.civ, tech.repeatable = f"Crucible Wonder {label}", 0, -1, 0
        tech.language_dll_name, tech.effect_id = name, len(d.effects) - 1
        tech.required_techs, tech.required_tech_count = (-1,) * 6, 0
        for rc in tech.resource_costs:
            rc.type, rc.amount, rc.flag = -1, 0, 0
        loc = tech.research_locations
        loc[0].location_id, loc[0].button_id, loc[0].research_time = WONDER, button, WONDER_TIME
        tech.research_locations = loc[:1]
        d.techs.append(tech)


def unit_mode_ids() -> tuple[int, int]:
    """(the Bowman's siege mode, the Mercenary Cavalry): added right after the ported units."""
    first = max(ported_ids().values()) + 1
    return first, first + 1


def mercenary_tech_id() -> int:
    """The Wonder tech that gives your team mercenary tokens: after the other Wonder techs."""
    return wonder_extra_tech_ids()[-1] + 1


def _unit_modes(d) -> None:
    """Kipchak-style Horse Archers, a switchable siege mode for Bowmen, and mercenaries limited by a token resource
    (unit test)."""
    siege_id, merc_id = len(d.civs[0].units), len(d.civs[0].units) + 1
    for civ in d.civs:
        u = civ.units
        ha = u[HORSE_ARCHER] if len(u) > HORSE_ARCHER else None
        if ha and ha.creatable:
            ha.creatable.projectile_spawning_area = KIPCHAK_SPREAD
            ha.creatable.total_projectiles = float(KIPCHAK_ARROWS)
            ha.creatable.max_total_projectiles = KIPCHAK_ARROWS
            ha.creatable.secondary_projectile_unit = CKN_ARROW
        bow, cav = (u[BOWMAN] if len(u) > BOWMAN else None), (u[CAVALRY] if len(u) > CAVALRY else None)
        if not (bow and cav):
            u += [None, None]
            continue
        siege = copy.deepcopy(bow)
        siege.id = siege.copy_id = siege.base_id = siege_id
        siege.name = "Bowman (siege mode)"
        siege.type_50.projectile_unit_id = CATAPULT_SHOT
        bonus = copy.deepcopy(siege.type_50.attacks[0])
        bonus.class_, bonus.amount = BUILDING_ARMOUR, SIEGE_BONUS
        siege.type_50.attacks.append(bonus)
        siege.trait, siege.nothing = SWITCH_TRAIT, BOWMAN
        bow.trait, bow.nothing = SWITCH_TRAIT, siege_id
        merc = copy.deepcopy(cav)
        merc.id = merc.copy_id = merc.base_id = merc_id
        merc.name, merc.enabled = "Mercenary Cavalry", 1
        costs = list(merc.creatable.resource_costs)
        costs[0].type, costs[0].amount, costs[0].flag = MERC_TOKEN, 1, 1
        costs[1].type, costs[1].amount, costs[1].flag = -1, 0, 0
        merc.creatable.resource_costs = tuple(costs)
        loc = merc.creatable.train_locations
        loc[0].unit_id, loc[0].button_id = TOWN_CENTER, MERC_BUTTON
        merc.creatable.train_locations = loc[:1]
        u += [siege, merc]
    # The Wonder tech: +5 mercenary tokens for your team (effect 11: a team resource change).
    template = d.techs[AXE_TECH]
    command = copy.deepcopy(next(c for e in d.effects for c in e.effect_commands if c.type == DISABLE_TECH))
    command.type, command.a, command.b, command.c, command.d = 11, MERC_TOKEN, 1, -1, float(MERC_GIFT)
    effect = copy.deepcopy(d.effects[template.effect_id])
    effect.effect_commands, effect.name = [command], "Crucible Wonder mercenaries"
    d.effects.append(effect)
    tech = copy.deepcopy(template)
    tech.name, tech.type, tech.civ, tech.repeatable = "Crucible Wonder mercenaries", 0, -1, 0
    tech.language_dll_name, tech.effect_id = d.civs[1].units[WONDER].language_dll_name, len(d.effects) - 1
    tech.required_techs, tech.required_tech_count = (-1,) * 6, 0
    for rc in tech.resource_costs:
        rc.type, rc.amount, rc.flag = -1, 0, 0
    loc = tech.research_locations
    loc[0].location_id, loc[0].button_id, loc[0].research_time = WONDER, MERC_TECH_BUTTON, WONDER_TIME
    tech.research_locations = loc[:1]
    d.techs.append(tech)


def _mule_cart_drop_site(data: dict) -> None:
    """dropsites.json: the ported Mule Cart takes what the Storage Pit and the Granary take. (Each villager job unit
    also has to list it in its drop sites; build_data_mod does that.)"""
    mule = ported_ids()[MULE_CART]
    pit = next(e for e in data["drop_site_list"] if e["building_id"] == STORAGE_PIT)
    granary = next(e for e in data["drop_site_list"] if e["building_id"] == GRANARY)
    targets = pit["target_list"] + [t for t in granary["target_list"] if t not in pit["target_list"]]
    data["drop_site_list"].append({"name": "Mule Cart", "building_id": mule,
                                   "worker_object_group": pit["worker_object_group"], "target_list": targets})


def _info(folder: Path, title: str, description: str) -> None:
    (folder / "info.json").write_text(json.dumps({"Author": "aoe2de-ror-crucible", "CacheStatus": 0,
                                                  "Description": description, "Title": title}), encoding="utf-8")


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def build_mission(out: Path, number: int) -> Path:
    """One test mission (both are the same apart from the title)."""
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 1
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "CASTLE", "human": True,
                                     "food": 1000, "wood": 1000, "gold": 1000, "stone": 1000,
                                     "population_cap": 200})
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            _add(s, 1, "TOWN_CENTER", 10, 10)
            for i in range(5):
                _add(s, 1, "VILLAGER_MALE", 14 + i, 14)
            _add(s, 1, "BARRACKS", 20, 8)
            _add(s, 1, "ACADEMY", 8, 20)
            for i in range(3):
                _add(s, 1, "CLUBMAN", 16 + i * 2, 18)
            # Houses with trees beside them, far from the Town Center: villagers drop wood at a House if they can.
            for x in (30, 33):
                _add(s, 1, "HOUSE", x, 30)
            for x in range(28, 37):
                for y in (34, 35):
                    _add(s, 0, "TREE_A", x, y)
            _add(s, 0, "FLAG_A", 44, 44)
            ctx = blocks.Ctx(s)
            ctx.trigger("Scout at the Barracks", [], [
                {"type": "enable_disable_object", "source_player": 1, "object_list_unit_id": "SCOUT", "enabled": 1},
                {"type": "modify_attribute", "source_player": 1, "object_list_unit_id": "SCOUT",
                 "object_attributes": TRAIN_LOCATION, "operation": SET, "quantity": 12},
                {"type": "modify_attribute", "source_player": 1, "object_list_unit_id": "SCOUT",
                 "object_attributes": TRAIN_BUTTON, "operation": SET, "quantity": SCOUT_BUTTON}])
            ctx.trigger("Finish", [{"type": "objects_in_area", "source_player": 1, "area": [42, 42, 47, 47],
                                    "quantity": 1}], [{"type": "declare_victory", "source_player": 1, "enabled": 1}])
            s.message_manager.instructions = f"Mission {number}. " + INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 20, "initial_player_view_y": 20})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{CAMPAIGN}_{number}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)


TOWER_INSTRUCTIONS = """Mission 3: garrisoned towers.

Two Sentry Towers, 5 garrison spots each. The LEFT tower gets what AoE2's towers have (by trigger, that tower \
only): an arrow limit of 6, a secondary arrow, and room for infantry as well as villagers. The RIGHT tower is \
unchanged, as the control. Villagers and bowmen get a garrison firepower of 1; hoplites keep 0. Enemy elephants \
stand in range and don't fight back.

Beside each tower: 5 villagers, 5 bowmen and 5 hoplites. Garrison them in turn and count the arrows per volley:
1. Empty: both towers should fire 1 arrow.
2. Villagers: each should add an arrow to the left tower. The right one?
3. Bowmen: with the data mod they have a garrison command. They should fit in the left tower (not the right one, \
which takes villagers only) and each add an arrow.
4. Hoplites: they should fit in the left tower but add no arrows.

Walk any unit onto the flag in the far corner to finish."""


def build_tower_mission(out: Path, number: int = 3) -> Path:
    """Do garrisoned units add arrows to a tower whose arrow limit is raised? One raised tower, one control."""
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "CASTLE", "human": True,
                                     "food": 1000, "wood": 1000, "gold": 1000, "stone": 1000,
                                     "population_cap": 200})
            player_set(o.handle, 2, {"civilization": "PERSIAN", "starting_age": "CASTLE", "ai": "none"})
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            towers = {}
            for name, x in (("raised", 14), ("control", 32)):
                towers[name] = _add(s, 1, "SENTRY_TOWER", x, 20)
                for i in range(5):
                    _add(s, 1, "VILLAGER_MALE", x - 4 + i * 2, 15)
                    _add(s, 1, "BOWMAN", x - 4 + i * 2, 13)
                    _add(s, 1, "HOPLITE", x - 4 + i * 2, 11)
            targets = [_add(s, 2, "WAR_ELEPHANT", x, 25) for x in (12, 14, 16, 30, 32, 34)]
            blocks.anchor(blocks.Ctx(s), player=2, at=(1, 46))
            _add(s, 1, "TOWN_CENTER", 40, 5)                 # keeps player 1 in the game
            _add(s, 0, "FLAG_A", 44, 44)
            ctx = blocks.Ctx(s)
            raised = {"type": "modify_object_attribute", "source_player": 1, "selected_object_ids": [towers["raised"]],
                      "operation": SET}
            # What AoE2's towers have and RoR's lack (data compared 2026-11-09): an arrow limit above 1, a secondary
            # projectile to fire the extra arrows with, and a garrison type that admits infantry (AoE2: 11).
            ctx.trigger("Garrisoned arrows on the left tower", [], [
                {**raised, "object_attributes": MAX_MISSILES, "quantity": 1 + GARRISON},
                {**raised, "object_attributes": SECONDARY_PROJECTILE, "quantity": TOWER_ARROW_2},
                {**raised, "object_attributes": GARRISON_TYPE, "quantity": VILLAGERS | INFANTRY}])
            # And what each garrisoned unit contributes: RoR gives every unit 0 (AoE2's archers 1). Hoplites stay at 0.
            ctx.trigger("Garrison firepower", [], [
                {"type": "modify_attribute_for_class", "source_player": 1, "object_group2": cls,
                 "object_attributes": GARRISON_FIREPOWER, "operation": SET, "quantity": 1, "quantity_float": 1.0}
                for cls in (CIVILIAN, ARCHER)])
            ctx.trigger("Passive targets", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": targets,
                 "attack_stance": "NO_ATTACK_STANCE"}])
            ctx.trigger("Finish", [{"type": "objects_in_area", "source_player": 1, "area": [42, 42, 47, 47],
                                    "quantity": 1}], [{"type": "declare_victory", "source_player": 1, "enabled": 1}])
            s.message_manager.instructions = TOWER_INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 23, "initial_player_view_y": 18})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{CAMPAIGN}_{number}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)


def build_campaign(out: Path) -> Path:
    camp = Campaign(CAMPAIGN)
    for n in (1, 2):
        p = build_mission(out, n)
        camp.scenarios.append(CampaignScenario(f"Mod test {n}", p.name, p.read_bytes()))
    p = build_tower_mission(out, 3)
    camp.scenarios.append(CampaignScenario("Garrisoned towers", p.name, p.read_bytes()))
    return camp.write(out / f"{CAMPAIGN}.aoe2campaign")


def build(out: Path) -> dict:
    mods = out / "mods"
    if mods.exists():
        shutil.rmtree(mods)
    return {"data_mod": build_data_mod(mods), "campaign": build_campaign(out)}


def install(res: dict) -> dict:
    """Copy the data mod into the profile's local mods and the campaign into RoR's campaign folder. Removes the first
    run's separate dropsites mod, which this test created and which would otherwise compete as a data mod."""
    from aoe2ed import game
    from aoe2ed.screens import mod_dir
    old = mod_dir(JSON_MOD, "ror")
    if (old / "info.json").is_file() and "aoe2de-ror-crucible" in (old / "info.json").read_text(encoding="utf-8"):
        shutil.rmtree(old)
    dest = mod_dir(res["data_mod"].name, "ror")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(res["data_mod"], dest)
    return {"data_mod": dest, "campaign": Path(game.install(res["campaign"], game="ror")["installed"])}
