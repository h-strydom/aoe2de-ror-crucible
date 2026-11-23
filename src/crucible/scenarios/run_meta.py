"""The meta upgrades in crucible_run (docs/meta-v2.md): loaded from the campaign bank at the start, each level giving
the player one more of something or unlocking units and techs (meta.py). Outside the Crucible campaign nothing is
loaded, so a standalone run gets none.

Buildings kept come from the base the Allies were handed, nearest the Town Center first (the Academy, Government
Center and Temple too); they change hands before the Allies' other buildings are destroyed (run.py).

Starting soldiers stand in slots by the Wonder, placed by hand (2026-11-17), as their line's latest upgrade bought:
melee Clubmen, then Axemen, Short, Broad, Long Swordsmen; Bowmen, then Improved, Composite Bowmen, Horse Archers;
Cavalry, then Heavy Cavalry; the Scout.

Upgrades unlock techs locked by run_rules (UNLOCKS, with the Market's, Storage Pit's, Government Center's and Temple's
rows by age) and units (UNIT_UNLOCKS, each once the player reaches its age). A tech is switched back on only once its
own prerequisites are met: Enable/Disable Technology skips them, so a tech switched on at the start could be
researched in any age. An age among them is checked as the player's current age (resource 6, as the unit unlocks
do), not as its tech researched: every Iron Age Storage Pit tech stayed off (playtest 2026-11-23). The Bronze and
Iron Ages come with hub tiers 3 and 4.

The towers and walls are handed over remade for the player (a unit that changes hands keeps its old owner's stats, so
the player's boons missed them): towers as the latest tower upgrade bought (Watch, Sentry, Guard), the Small Walls as
Small or Medium Walls, undamaged; the camp's Fortified Walls with the Fortified Wall upgrade.

The Wonder's upgrades: starting resources (triggers), and the Town Centers' work rate, the resource densities (RoR's
gather bonuses, multiplied: GATHER), and the villagers' cost (XS, at the start).
"""

from math import dist

from aoe2ed import blocks

from crucible import meta

VILLAGER_MALE, VILLAGER_FEMALE = 83, 293
HOUSE, SCOUT = 70, 448
SMALL_WALL, MEDIUM_WALL, FORTIFIED_WALL = 72, 117, 155
TOWERS = (79, 234, 235, 236)  # Watch, Sentry, Guard, Ballista Tower
LOOKS_ONLY = (HOUSE,)  # kept by a change of hands (no buttons to lose); the rest are created anew
AGE_TECHS = ((1, 101), (2, 102), (3, 103))  # (the age reached, its tech): Tool, Bronze, Iron
UPGRADE_UNIT = 3  # effect command
CURRENT_AGE = 6  # resource
TRAIN_TIME, FOOD_COST = 101, 103  # unit attributes
WHALE_CLASS = 63
SLOTS = {  # where starting soldiers stand: tiles, in the order they fill
    "melee": ((104, 114), (105, 114), (105, 115), (104, 115), (103, 114)),
    "ranged": ((105, 117), (105, 118), (104, 118), (104, 117), (103, 118)),
    "scout": ((105, 120),),
    "cavalry": ((103, 120), (103, 121), (103, 122)),
    "siege": ((102, 116),),
}
STARTING = ((HOUSE, meta.STARTING_HOUSES),)  # kept in every run: the type, how many (nearest the Town Center)
KEPT = {  # upgrade -> (the building type each level keeps, how many of that type nearer the Town Center to skip)
    meta.HOUSES.key: (HOUSE, meta.STARTING_HOUSES),
    meta.GRANARY_UPGRADE.key: (meta.GRANARY, 0),
    meta.STORAGE_PIT_UPGRADE.key: (meta.STORAGE_PIT, 0),
    meta.BARRACKS_UPGRADE.key: (meta.BARRACKS, 0),
    meta.SECOND_BARRACKS.key: (meta.BARRACKS, 1),
    meta.MARKET_UPGRADE.key: (meta.MARKET, 0),
    meta.ARCHERY_RANGE_UPGRADE.key: (meta.ARCHERY_RANGE, 0),
    meta.STABLE_UPGRADE.key: (meta.STABLE, 0),
    meta.ACADEMY_UPGRADE.key: (meta.ACADEMY, 0),
    meta.GOVERNMENT_CENTER_UPGRADE.key: (meta.GOVERNMENT_CENTER, 0),
    meta.TEMPLE_UPGRADE.key: (meta.TEMPLE, 0),
}

# Upgrade -> the techs it unlocks (each still waits for its prerequisites).
UNLOCKS = {
    meta.BRONZE_AGE.key: (102,),
    meta.IRON_AGE.key: (103,),
    meta.AXE.key: (63,),
    meta.TOWER.key: (16,),
    meta.SENTRY_TOWER.key: (12,),
    meta.GUARD_TOWER.key: (15,),  # no Ballista Tower
    meta.WHEEL.key: (28,),
    meta.BROAD_SWORD.key: (65,),
    meta.IMPROVED_BOW.key: (56,),
    meta.COMPOSITE_BOW.key: (57,),
    meta.LONG_SWORD.key: (66,),
    meta.HEAVY_CAVALRY_UPGRADE.key: (71,),
    meta.PHALANGITE.key: (73,),
    meta.CATAPULT_UPGRADE.key: (54,),
    meta.LEGIONARY_UPGRADE.key: (77,),
    meta.HEAVY_HORSE_ARCHERS.key: (38,),
    meta.CATAPHRACTS.key: (78,),
    meta.ARMORED_ELEPHANTS.key: (125,),
    meta.SCYTHE_CHARIOTS.key: (126,),
    meta.CENTURIONS.key: (79,),
    meta.HEAVY_CATAPULTS.key: (36,),
    meta.HELEPOLISES.key: (27,),
}
# Upgrade -> (building, age) whose techs of that age it unlocks: the buildings' rows.
ROWS = {
    meta.MARKET_TECHS.key: (meta.MARKET, 1),
    meta.MARKET_TECHS_2.key: (meta.MARKET, 2),
    meta.MARKET_TECHS_3.key: (meta.MARKET, 3),
    meta.STORAGE_PIT_TECHS.key: (meta.STORAGE_PIT, 1),
    meta.STORAGE_PIT_TECHS_2.key: (meta.STORAGE_PIT, 2),
    meta.STORAGE_PIT_TECHS_3.key: (meta.STORAGE_PIT, 3),
    meta.GOVERNMENT_TECHS.key: (meta.GOVERNMENT_CENTER, 2),
    meta.GOVERNMENT_TECHS_2.key: (meta.GOVERNMENT_CENTER, 3),
    meta.TEMPLE_TECHS.key: (meta.TEMPLE, 2),
    meta.TEMPLE_TECHS_2.key: (meta.TEMPLE, 3),
    meta.DOCK_TECHS.key: (meta.DOCK, 2),
    meta.DOCK_TECHS_2.key: (meta.DOCK, 3),
}
OWN_UPGRADE = (28,)  # Wheel: its own upgrade, not in the Market's row
NEVER = (19,)  # Writing: shared vision with allies, and the Traders (everyone's ally) see the whole map
# The gather bonuses (player resources) each Wonder density upgrade multiplies: food (and fishing), wood, mining
GATHER = {"food": (190, 219), "wood": (189,), "mining": (47, 79)}
# Upgrade -> (unit, the age the player needs) it unlocks.
UNIT_UNLOCKS = {
    meta.TOWER.key: ((79, 1),),  # building Watch Towers (the tech alone didn't, playtest 2026-11-23)
    meta.ACADEMY_UPGRADE.key: ((meta.ACADEMY, 2), (93, 2)),  # and Hoplites
    meta.SIEGE_WORKSHOP_UPGRADE.key: ((meta.SIEGE_WORKSHOP, 2), (280, 2)),  # and Stone Throwers
    meta.TEMPLE_UPGRADE.key: ((meta.TEMPLE, 2), (125, 2)),  # and Priests
    meta.GOVERNMENT_CENTER_UPGRADE.key: ((meta.GOVERNMENT_CENTER, 2),),
    meta.WHEEL.key: ((1370, 2), (5, 2)),  # Chariots, Chariot Archers
    meta.SHORT_SWORD.key: ((74, 2),),
    meta.CAMEL.key: ((329, 2),),
    meta.CAVALRY_UPGRADE.key: ((38, 2),),
    meta.HORSE_ARCHERS.key: ((39, 3),),
    meta.BALLISTA_UPGRADE.key: ((279, 3),),
    meta.ELEPHANT_ARCHERS.key: ((873, 3),),
    meta.WAR_ELEPHANTS.key: ((1132, 3),),
}
# Starting soldiers: a line's units by the upgrade that brings each (none: from the start).
MELEE_LINE = (
    ("", meta.CLUBMAN),
    (meta.AXE.key, meta.AXEMAN),
    (meta.SHORT_SWORD.key, meta.SHORT_SWORDSMAN),
    (meta.BROAD_SWORD.key, meta.BROAD_SWORDSMAN),
    (meta.LONG_SWORD.key, meta.LONG_SWORDSMAN),
)
RANGED_LINE = (
    ("", meta.BOWMAN),
    (meta.IMPROVED_BOW.key, meta.IMPROVED_BOWMAN),
    (meta.COMPOSITE_BOW.key, meta.COMPOSITE_BOWMAN),
    (meta.HORSE_ARCHERS.key, meta.HORSE_ARCHER),
)
CAVALRY_LINE = (("", meta.CAVALRY), (meta.HEAVY_CAVALRY_UPGRADE.key, meta.HEAVY_CAVALRY))
TOWER_LINE = ((meta.TOWER.key, 79), (meta.SENTRY_TOWER.key, 234), (meta.GUARD_TOWER.key, 235))
WALL_LINE = ((meta.WALLS.key, SMALL_WALL), (meta.MEDIUM_WALL.key, MEDIUM_WALL))
STARTING_RESOURCES = {"FOOD_STORAGE": 50, "WOOD_STORAGE": 50, "GOLD_STORAGE": 20, "STONE_STORAGE": 20}  # a level
TOWN_CENTERS = (109, 71, 141, 142)  # the Town Center's look in each age: a building's work rate goes on every one
WORK_RATE = 13  # unit attribute: a building's training and research speed
DENSITY = 2  # how many times as much a density upgrade gives
VILLAGER_COST = 5  # food less a level


def _age(data, tech: int) -> int:
    required = data.techs[tech].required_techs

    return next((age for age, age_tech in reversed(AGE_TECHS) if age_tech in required), 0)


def _chain(chains: dict[int, dict[int, int]], building: int) -> set[int]:
    for first, chain in chains.items():
        if building == first or building in chain.values():
            return {first, *chain.values()}

    return {building}


def unlocks(data) -> dict[str, dict[int, list[int]]]:
    """Upgrade -> each tech it unlocks -> that tech's prerequisites (all needed: RoR's counts match)."""
    from crucible.scenarios.run_rules import techs_at

    chains = age_chains(data)
    techs = {key: tuple(found) for key, found in UNLOCKS.items()}

    for key, (building, age) in ROWS.items():
        at = sorted({t for place in _chain(chains, building) for t in techs_at(data, place)})
        first = min(a for b, a in ROWS.values() if b == building)  # a tech with no age (Jihad) joins the first row
        techs[key] = tuple(t for t in at if (_age(data, t) or first) == age and t not in (*OWN_UPGRADE, *NEVER))

    return {
        key: {tech: [r for r in data.techs[tech].required_techs if r >= 0] for tech in found}
        for key, found in techs.items()
    }


def _prerequisite(tech: int, player: int) -> dict:
    """A condition: `tech` researched, or for an age tech, the player in that age."""
    age = next((age for age, age_tech in AGE_TECHS if age_tech == tech), None)

    if age is not None:
        return {"type": "accumulate_attribute", "source_player": player, "attribute": CURRENT_AGE, "quantity": age}

    return {"type": "research_technology", "source_player": player, "technology": tech}


def _at_least(key: str, level: int) -> list[dict]:
    return [{"type": "variable_value", "variable": key, "comparison": "LARGER_OR_EQUAL", "quantity": level}]


def _below(key: str, level: int) -> list[dict]:
    return [{"type": "variable_value", "variable": key, "comparison": "LESS", "quantity": level}]


def _latest(line: tuple, n: int) -> list[dict]:
    """Conditions: the nth of `line` is the latest bought (its upgrade bought, the next one not)."""
    key = line[n][0]
    later = line[n + 1][0] if n + 1 < len(line) else ""

    return (_at_least(key, 1) if key else []) + (_below(later, 1) if later else [])


def age_chains(data) -> dict[int, dict[int, int]]:
    """A building's Age1 unit -> the unit each age makes it ({1: Age2, 2: Age3, 3: Age4}), read from the age techs
    (ids aren't in age order: the Barracks is 12, 498, 132)."""
    chains: dict[int, dict[int, int]] = {}

    for age, tech in AGE_TECHS:
        for command in data.effects[data.techs[tech].effect_id].effect_commands:
            if command.type == UPGRADE_UNIT:
                chains.setdefault(command.a, {})[age] = command.b

    return chains


def _keep(ctx, name: str, conditions: list[dict], unit, allies: int, player: int) -> None:
    """Make one of the Allies' buildings the player's. A building given to a player keeps the look of the age it had
    (AoE's rule), so a working one (Barracks, Granary, Storage Pit) is removed and, a second later, created anew for the
    player on its tile, to age up like one the player built. Nothing else may stand on that tile: a building isn't
    created over anything (a berry bush under the arena's Granary kept it from coming back, so the bush is gone).
    (Replacing it with the next age's unit lost its buttons: units train at the Age1 Barracks, 12, not at the Age2
    one.) A house only looks, so it changes hands and _ages replaces it at each age."""
    if unit.unit_const in LOOKS_ONLY:
        move = {
            "type": "change_ownership",
            "source_player": allies,
            "target_player": player,
            "selected_object_ids": [unit.reference_id],
        }
        ctx.trigger(name, conditions, [move])

        return

    _remake(ctx, name, conditions, [unit], allies, player)


def _remake(ctx, name: str, conditions: list[dict], units: list, allies: int, player: int, kind: int = -1) -> None:
    """Remove the Allies' `units`, then a second later create the same (or `kind`) for the player on their tiles."""
    placed = f"{name} placed"
    remove = {"type": "remove_object", "source_player": allies, "selected_object_ids": [u.reference_id for u in units]}
    create = [
        {
            "type": "create_object",
            "object_list_unit_id": kind if kind >= 0 else unit.unit_const,
            "source_player": player,
            "location": [int(unit.x), int(unit.y)],
        }
        for unit in units
    ]
    later = {"type": "activate_trigger", "trigger_id": placed}
    ctx.triggers(
        {"name": name, "conditions": conditions, "effects": [remove, later]},
        {"name": placed, "enabled": False, "conditions": [{"type": "timer", "timer": 1}], "effects": create},
    )


def _ages(ctx, kept: list, chains: dict[int, dict[int, int]], player: int) -> None:
    """At each age the player reaches, each kept house is replaced, on its own tile, by that age's."""
    for age, _ in AGE_TECHS:
        effects = []

        for unit in kept:
            chain = {0: unit.unit_const, **chains.get(unit.unit_const, {})}
            before = max((a for a in chain if a < age), default=0)

            if age in chain:
                tile = [int(unit.x), int(unit.y), int(unit.x), int(unit.y)]
                effects.append(
                    {
                        "type": "replace_object",
                        "source_player": player,
                        "target_player": player,
                        "object_list_unit_id": chain[before],
                        "object_list_unit_id_2": chain[age],
                        "area": tile,
                    }
                )

        ctx.trigger(
            f"Meta: kept buildings to age {age}",
            [{"type": "accumulate_attribute", "source_player": player, "attribute": CURRENT_AGE, "quantity": age}],
            effects,
        )


def add(
    ctx,
    s,
    *,
    player: int,
    allies: int,
    town_center: tuple[float, float],
    villagers,
    chains: dict[int, dict[int, int]],
    unlocked: dict[str, dict[int, list[int]]],
) -> None:
    """`villagers`: where each extra villager starts (tile centres), in order. `chains`: age_chains(). `unlocked`:
    unlocks()."""
    blocks.bank.load(ctx, dict.fromkeys(meta.KEYS, 0), name="Meta: load upgrades")

    for level, (x, y) in enumerate(villagers[: meta.VILLAGERS.levels], start=1):
        unit = VILLAGER_MALE if level % 2 else VILLAGER_FEMALE
        ctx.trigger(
            f"Meta: villager {level}",
            _at_least(meta.VILLAGERS.key, level),
            [
                {
                    "type": "create_object",
                    "object_list_unit_id": unit,
                    "source_player": player,
                    "location": [int(x), int(y)],
                }
            ],
        )

    kept = []

    def nearest(building: int) -> list:
        units = (u for u in s.unit_manager.units[allies] if u.unit_const == building)

        return sorted(units, key=lambda u: dist((u.x, u.y), town_center))

    for building, count in STARTING:
        for n, unit in enumerate(nearest(building)[:count], start=1):
            _keep(ctx, f"Meta: starting building {building} {n}", [], unit, allies, player)

            if building in LOOKS_ONLY:
                kept.append(unit)

    for key, (building, skip) in KEPT.items():
        upgrade = next(u for u in meta.UPGRADES if u.key == key)
        candidates = nearest(building)[skip : skip + upgrade.levels]
        if building in LOOKS_ONLY:
            kept += candidates

        for level, unit in enumerate(candidates, start=1):
            _keep(ctx, f"Meta: {upgrade.title} {level}", _at_least(key, level), unit, allies, player)

    _ages(ctx, kept, chains, player)
    _soldiers(ctx, player)

    for key, techs in unlocked.items():
        for tech, required in techs.items():
            ctx.trigger(
                f"Meta: {meta.TITLES[key]} unlocks {tech}",
                _at_least(key, 1) + [_prerequisite(r, player) for r in required],
                [{"type": "enable_disable_technology", "source_player": player, "technology": tech, "enabled": 1}],
            )

    for key, units in UNIT_UNLOCKS.items():
        for unit, age in units:
            ctx.trigger(
                f"Meta: {meta.TITLES[key]} unlocks unit {unit}",
                _at_least(key, 1)
                + [
                    {"type": "accumulate_attribute", "source_player": player, "attribute": CURRENT_AGE, "quantity": age}
                ],
                [{"type": "enable_disable_object", "source_player": player, "object_list_unit_id": unit, "enabled": 1}],
            )

    _defences(ctx, s, allies, player)
    _wonder(ctx, player)


def _defences(ctx, s, allies: int, player: int) -> None:
    """The base's towers as the latest tower upgrade bought, its Small Walls as Small or Medium Walls (undamaged:
    run_xs damages only the Allies'), and the camp's Fortified Walls with their own upgrade."""
    towers = [u for u in s.unit_manager.units[allies] if u.unit_const in TOWERS]
    walls = [u for u in s.unit_manager.units[allies] if u.unit_const == SMALL_WALL]
    fortified = [u for u in s.unit_manager.units[allies] if u.unit_const == FORTIFIED_WALL]

    for n, (key, kind) in enumerate(TOWER_LINE):
        later = _below(TOWER_LINE[n + 1][0], 1) if n + 1 < len(TOWER_LINE) else []
        conditions = _at_least(meta.TOWER.key, 1) + _at_least(key, 1) + later
        _remake(ctx, f"Meta: towers as {kind}", conditions, towers, allies, player, kind)

    for n, (key, kind) in enumerate(WALL_LINE):
        later = _below(WALL_LINE[n + 1][0], 1) if n + 1 < len(WALL_LINE) else []
        conditions = _at_least(meta.WALLS.key, 1) + _at_least(key, 1) + later
        _remake(ctx, f"Meta: walls as {kind}", conditions, walls, allies, player, kind)

    if fortified:
        _remake(ctx, "Meta: Fortified Walls", _at_least(meta.FORTIFIED_WALL.key, 1), fortified, allies, player)


def _create(unit: int, player: int, tiles) -> list[dict]:
    return [
        {"type": "create_object", "object_list_unit_id": unit, "source_player": player, "location": list(tile)}
        for tile in tiles
    ]


def _soldiers(ctx, player: int) -> None:
    """3 melee in the first melee slots (Clubmen), 2 more with the Axemen upgrade; 3 then 2 Bowmen; a Cavalry a level;
    the Scout. Each as its line's latest upgrade bought (MELEE_LINE...)."""
    melee, ranged, cavalry = SLOTS["melee"], SLOTS["ranged"], SLOTS["cavalry"]
    first = melee[: meta.CLUBMEN_PER_LEVEL]
    more = melee[len(first) : len(first) + meta.AXEMEN.amounts[0]]

    for n, (_, unit) in enumerate(MELEE_LINE):
        latest = _latest(MELEE_LINE, n)
        ctx.trigger(f"Meta: melee {unit}", _at_least(meta.CLUBMEN.key, 1) + latest, _create(unit, player, first))
        ctx.trigger(f"Meta: more melee {unit}", _at_least(meta.AXEMEN.key, 1) + latest, _create(unit, player, more))

    for n, (_, unit) in enumerate(RANGED_LINE):
        done = 0

        for level, amount in enumerate(meta.BOWMEN.amounts, start=1):
            tiles, done = ranged[done : done + amount], done + amount
            conditions = _at_least(meta.BOWMEN.key, level) + _latest(RANGED_LINE, n)
            ctx.trigger(f"Meta: Bowmen {level} as {unit}", conditions, _create(unit, player, tiles))

    for n, (_, unit) in enumerate(CAVALRY_LINE):
        for level, tile in enumerate(cavalry[: meta.CAVALRY_UPGRADE.levels], start=1):
            conditions = _at_least(meta.CAVALRY_UPGRADE.key, level) + _latest(CAVALRY_LINE, n)
            ctx.trigger(f"Meta: Cavalry {level} as {unit}", conditions, _create(unit, player, [tile]))

    ctx.trigger("Meta: Scout", _at_least(meta.SCOUT.key, 1), _create(SCOUT, player, SLOTS["scout"]))


def _variable_id(ctx, name: str) -> int:
    ctx.var(name)

    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def _wonder(ctx, player: int) -> None:
    """Starting resources (a trigger a level); the Town Centers' work rate, densities and the villagers'
    cost (XS)."""
    for level in range(1, meta.STARTING_RESOURCES.levels + 1):
        ctx.trigger(
            f"Meta: starting resources {level}",
            _at_least(meta.STARTING_RESOURCES.key, level),
            [
                {
                    "type": "modify_resource",
                    "tribute_list": resource,
                    "source_player": player,
                    "operation": "ADD",
                    "quantity": amount,
                }
                for resource, amount in STARTING_RESOURCES.items()
            ],
        )

    def level(upgrade: meta.Upgrade) -> str:
        return f"xsTriggerVariable({_variable_id(ctx, upgrade.key)})"

    density = {"food": meta.FOOD_DENSITY, "wood": meta.WOOD_DENSITY, "mining": meta.MINING_DENSITY}
    calls = "\n".join(
        f"    crucibleMetaGather({resource}, {level(density[kind])});"
        for kind, resources in GATHER.items()
        for resource in resources
    )
    villagers = "\n".join(
        f"    xsEffectAmount(cAddAttribute, {unit}, {FOOD_COST}, 0.0 - {VILLAGER_COST} * cost, {player});"
        for unit in (VILLAGER_MALE, VILLAGER_FEMALE)
    )
    rate = f"1.0 + 0.01 * {meta.TOWN_CENTER_SPEEDS} * busy"
    town_centers = "\n".join(
        f"    xsEffectAmount(cMulAttribute, {unit}, {WORK_RATE}, {rate}, {player});" for unit in TOWN_CENTERS
    )
    ctx.xs(f"""// ---- crucible run: the Wonder's upgrades ----
// A gather bonus (a player resource: how much a gatherer gets per unit a pile loses) times DENSITY with its density
// upgrade, as RoR's "Resources last" bonuses multiply them. (Setting each pile's amount from XS didn't show in play,
// 2026-11-23.)
void crucibleMetaGather(int resource = -1, int dense = 0) {{
    if (dense > 0) {{
        xsSetPlayerAttribute({player}, resource, xsPlayerAttribute({player}, resource) * {DENSITY});
    }}
}}

rule crucibleMetaWonder
    active
    minInterval 1
{{
    if (xsGetTime() < 2) {{
        return;  // after the bank's load
    }}

{calls}
    int busy = {level(meta.TOWN_CENTER_SPEED)};
{town_centers}
    int cost = {level(meta.VILLAGER_COST)};
{villagers}
    xsDisableSelf();
}}
""")
