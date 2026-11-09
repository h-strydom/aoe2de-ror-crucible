"""The data mod test: can a Crucible campaign depend on a mod for what triggers can't do?

Builds one local data mod and a two-mission test campaign:

- **Crucible Test Data**: Return of Rome's own data file and `dropsites.json`, with visible changes. Hoplites have
  999 hit points (120 normally) and Axemen 400 (50). The Greek civilization loses its bonuses (Hoplites cost
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
HP = {93: 999, 531: 400}                   # Hoplite, Axeman (Clubmen become Axemen when a Bronze Age start
                                           # researches Axe)
HOPLITE = 93
GREEK = 2                                  # civ index in RoR's data
HOUSE_IDS = [70, 463, 464, 465]            # the House and its age looks
STORAGE_PIT = 562
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
SIZE = 48

INSTRUCTIONS = """Crucible mod test.

Before starting: in Mods > Installed Mods, enable "Crucible Test Data" (and disable "Crucible Test Dropsites" if \
it's still there), restart the game, then on the campaign screen set Data Mod to "Crucible Test Data".

1. HIT POINTS: select a Hoplite and an Axeman. With the data mod: 999 and 400. Without: 120 and 50.
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
        # Resource test: fishing boats told to take wood (not fish) from fish. Does a mismatched gather do anything?
        for uid in FISHING_BOATS:
            unit = civ.units[uid] if len(civ.units) > uid else None
            for t in (unit.bird.tasks if unit and unit.bird else []):
                if t.action_type == GATHER_ACTION and t.resource_in == FISH:
                    t.resource_in = WOOD
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
    (out.parent / "dropsites.json").write_text(json.dumps(data, indent=4), encoding="utf-8")
    _info(folder, DATA_MOD, "Crucible test: Hoplites 999 HP, Axemen 400 HP, Greeks without bonuses, Houses take "
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
