"""The Legion's outposts come alive (docs/outposts.md): phase 2, each defends itself and grows.

Each of the six bases (`bases.BASES`) rolls an archetype at the start, as a wave lane does (`wave_table.ARCHETYPES`),
and fields its paths' lines up to the Legion's age (`crucibleWaveAge`, from waves.xs): a higher level fields later
lines. Outposts never roll upgrades of their own; the Legion's are shared, so they have the waves'.

Every second (XS) an outpost watches its buildings and defenders: any HP lost, or a defender killed, and it's
harassed: its defenders attack-move to where it was hit. Every few minutes it takes a turn (TICK, TICK_SPREAD): it
grows (GROW a level a turn, GROW_HARASSED if harassed within TURTLE seconds), and unless harassed tops up its
defenders (target: START_DEFENDERS, + a level's and an age's worth, at most MAX_DEFENDERS), SPAWN_PER_TICK a turn, and
calls them home. Once all its buildings are gone (`bases.buildings`: not walls or farms) it does nothing more.

Markers (2026-11-23): the Legion's female villagers on land and its Light Transports at sea mark where the outposts'
attack waves will come from (phase 4); the run takes them off the map and keeps their tiles.
"""

import math

from AoE2ScenarioParser.datasets.terrains import TerrainId

from crucible.datamod.mod import source_dat
from crucible.scenarios import bases
from crucible.scenarios import wave_table as table

LEGION = 3
LAND_MARKER = 293  # VFBAS, the female villager
SEA_MARKER = 545  # Light Transport

DEBUG = True  # chat says each outpost's turns: for the playtest only (outposts are meant to be silent)
START_AT = 10  # seconds: the first look (after waves.xs has set up)
FIRST_TICK, TICK, TICK_SPREAD = 60, 120, 120  # seconds: the first turn; then every TICK + 0-TICK_SPREAD
TURTLE = 180  # seconds after the last harassment an outpost stays turtled
GROW, GROW_HARASSED = 10, 3  # growth points a turn (10 a level): left alone, harassed
START_DEFENDERS = 3
LEVELS_PER_DEFENDER = 2
DEFENDERS_PER_AGE = 2
DIFFICULTY_DEFENDERS = 2  # more for each step of difficulty above Standard
MAX_DEFENDERS = 25
SPAWN_PER_TICK = 3
LEVELS_PER_LINE = 4  # a level step of this many moves an outpost's units a line on
SPAWN_TILES = 6
AGES = len(table.Age)
SLOTS = (table.Slot.MELEE, table.Slot.RANGED)
WATER = {t.value for t in TerrainId if "WATER" in t.name}
BLOCKED = WATER | {t.value for t in TerrainId if "FOREST" in t.name}
BUILDING = 80


def take(s) -> dict[str, list[tuple[float, float]]]:
    """Remove the markers from scenario `s`; returns their tiles: {"land": [...], "sea": [...]}."""
    units = s.unit_manager.units[LEGION]
    found = {"land": [], "sea": []}
    markers = []

    for unit in units:
        kind = {LAND_MARKER: "land", SEA_MARKER: "sea"}.get(unit.unit_const)

        if kind:
            found[kind].append((unit.x, unit.y))
            markers.append(unit)

    for unit in markers:
        s.unit_manager.remove_unit(unit=unit)

    return found


def pools() -> list[list[int]]:
    """For each (archetype, slot, age), index (a * 2 + slot) * AGES + age: the unit ids its first path fields by that
    age, in path order (each stage's families, each family's lines): later is better."""
    found = []

    for archetype in table.ARCHETYPES:
        for slot in SLOTS:
            path = archetype.paths[slot][0]

            for age in table.Age:
                found.append(
                    [
                        table.unit_id(line.unit)
                        for stage in path
                        for name in stage
                        if name
                        for line in table.BY_NAME[name].lines
                        if line.age <= age
                    ]
                )

    return found


def spawn_tiles(s, home: tuple[float, float], near: int = SPAWN_TILES) -> list[tuple[int, int]]:
    """Land tiles near `home` clear of any unit (buildings by a wider margin): where defenders appear."""
    data = source_dat().civs[1].units
    mm = s.map_manager
    taken = []

    for player in s.unit_manager.units:
        for u in player:
            unit = data[u.unit_const] if u.unit_const < len(data) else None
            taken.append((u.x, u.y, 2.5 if unit and unit.type == BUILDING else 1.2))

    def free(x: int, y: int) -> bool:
        if mm.get_tile(x, y).terrain_id in BLOCKED:
            return False

        return all(math.dist((x + 0.5, y + 0.5), (ux, uy)) > r for ux, uy, r in taken)

    hx, hy = home
    size = mm.map_size
    tiles = [
        (x, y)
        for x in range(max(0, int(hx) - 12), min(size, int(hx) + 13))
        for y in range(max(0, int(hy) - 12), min(size, int(hy) + 13))
        if free(x, y)
    ]
    tiles.sort(key=lambda t: math.dist((t[0] + 0.5, t[1] + 0.5), home))

    if len(tiles) < near:
        raise ValueError(f"only {len(tiles)} free land tiles near {home}")

    return tiles[:near]


def _ints(name: str, values: list[int]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateInt({max(len(values), 1)}, -1, "{name}");']

    return lines + [f"    xsArraySetInt({name}, {n}, {v});" for n, v in enumerate(values)]


def _floats(name: str, values: list[float]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateFloat({max(len(values), 1)}, 0.0, "{name}");']

    return lines + [f"    xsArraySetFloat({name}, {n}, {float(v)});" for n, v in enumerate(values)]


def _strings(name: str, values: list[str]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateString({max(len(values), 1)}, "", "{name}");']

    return lines + [f'    xsArraySetString({name}, {n}, "{v}");' for n, v in enumerate(values)]


def xs(s) -> str:
    """The outposts' XS (after waves.xs: it reads crucibleWaveAge and crucibleWaveFactor)."""
    homes, buildings, starts, tiles = [], [], [], []

    for _, box in bases.BASES:
        found = bases.buildings(s, box)
        home = (sum(u.x for u in found) / len(found), sum(u.y for u in found) / len(found))
        homes.append(home)
        starts.append(len(buildings))
        buildings += [u.reference_id for u in found]
        tiles += spawn_tiles(s, home)

    starts.append(len(buildings))
    pool_start, pool_units = [], []

    for units in pools():
        pool_start.append(len(pool_units))
        pool_units += units

    pool_start.append(len(pool_units))
    setup = [
        *_floats("crucibleOutpostHomeX", [x for x, _ in homes]),
        *_floats("crucibleOutpostHomeY", [y for _, y in homes]),
        *_ints("crucibleOutpostBuildingStart", starts),
        *_ints("crucibleOutpostBuildings", buildings),
        *_floats("crucibleOutpostTileX", [x + 0.5 for x, _ in tiles]),
        *_floats("crucibleOutpostTileY", [y + 0.5 for _, y in tiles]),
        *_ints("crucibleOutpostPoolStart", pool_start),
        *_ints("crucibleOutpostPoolUnits", pool_units),
        *_ints("crucibleOutpostMain", [int(a.main) for a in table.ARCHETYPES]),
        *_strings("crucibleOutpostName", [name for name, _ in bases.BASES]),
        *_strings("crucibleOutpostArchetypeName", [a.name for a in table.ARCHETYPES]),
    ]
    nl = "\n"

    return f"""// ---- crucible run: the Legion's outposts (docs/outposts.md, scenarios/outposts.py) ----
const int cCrucibleOutposts = {len(bases.BASES)};
const int cCrucibleOutpostMax = {MAX_DEFENDERS};
const int cCrucibleOutpostTiles = {SPAWN_TILES};
const int cCrucibleOutpostAges = {AGES};
const bool cCrucibleOutpostDebug = {"true" if DEBUG else "false"};
int crucibleOutpostHomeX = -1;
int crucibleOutpostHomeY = -1;
int crucibleOutpostBuildingStart = -1;  // by outpost: where its buildings start in crucibleOutpostBuildings (+1: end)
int crucibleOutpostBuildings = -1;  // unit ids
int crucibleOutpostBuildingHp = -1;  // by building: its HP last second
int crucibleOutpostTileX = -1;  // by outpost * cCrucibleOutpostTiles: where defenders appear
int crucibleOutpostTileY = -1;
int crucibleOutpostPoolStart = -1;  // by (archetype * 2 + slot) * ages + age (+1: end)
int crucibleOutpostPoolUnits = -1;
int crucibleOutpostMain = -1;  // by archetype: its main slot
int crucibleOutpostName = -1;
int crucibleOutpostArchetypeName = -1;
int crucibleOutpostArchetype = -1;  // by outpost
int crucibleOutpostGrowth = -1;  // by outpost: 10 a level
int crucibleOutpostAlive = -1;  // by outpost: 1 while a building stands
int crucibleOutpostNextTurn = -1;  // by outpost: seconds
int crucibleOutpostHarassedAt = -1;  // by outpost: seconds, -1 never
int crucibleOutpostSpawned = -1;  // by outpost: units spawned (picks the next tile)
int crucibleOutpostDefenders = -1;  // by outpost * cCrucibleOutpostMax: unit ids, -1 a free place
int crucibleOutpostDefenderHp = -1;
int crucibleOutpostIds = -1;  // a reused list of ids for xsTaskUnits

float crucibleOutpostHp(int id = -1) {{
    float hp = xsGetUnitProperty(id, cUnitHitpoints);

    if (hp < 0.0) {{
        return (0.0);
    }}

    return (hp);
}}

vector crucibleOutpostHome(int o = 0) {{
    return (xsVectorSet(xsArrayGetFloat(crucibleOutpostHomeX, o), xsArrayGetFloat(crucibleOutpostHomeY, o), 0.0));
}}

int crucibleOutpostLevel(int o = 0) {{
    return (xsArrayGetInt(crucibleOutpostGrowth, o) / 10);
}}

bool crucibleOutpostTurtled(int o = 0) {{
    int at = xsArrayGetInt(crucibleOutpostHarassedAt, o);

    return ((at >= 0) && (xsGetTime() - at < {TURTLE}));
}}

int crucibleOutpostCount(int o = 0) {{
    int found = 0;

    for (d = 0; < cCrucibleOutpostMax) {{
        if (xsArrayGetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + d) >= 0) {{
            found++;
        }}
    }}

    return (found);
}}

int crucibleOutpostTarget(int o = 0) {{
    int target = {START_DEFENDERS} + crucibleOutpostLevel(o) / {LEVELS_PER_DEFENDER};

    target = target + crucibleWaveAge * {DEFENDERS_PER_AGE} + (crucibleWaveFactor - 1) * {DIFFICULTY_DEFENDERS};

    if (target > cCrucibleOutpostMax) {{
        return (cCrucibleOutpostMax);
    }}

    return (target);
}}

// Its archetype's unit for `slot` at the Legion's age: later lines with level.
int crucibleOutpostUnit(int o = 0, int slot = 0) {{
    int k = (xsArrayGetInt(crucibleOutpostArchetype, o) * 2 + slot) * cCrucibleOutpostAges + crucibleWaveAge;
    int start = xsArrayGetInt(crucibleOutpostPoolStart, k);
    int count = xsArrayGetInt(crucibleOutpostPoolStart, k + 1) - start;
    int pick = crucibleOutpostLevel(o) / {LEVELS_PER_LINE} + crucibleWaveAge;

    if (count <= 0) {{
        return (-1);
    }}

    if (pick > count - 1) {{
        pick = count - 1;
    }}

    return (xsArrayGetInt(crucibleOutpostPoolUnits, start + pick));
}}

// Every defender of `o` attack-moves to `at`.
void crucibleOutpostSend(int o = 0, vector at = cInvalidVector) {{
    int n = 0;
    int id = -1;

    for (d = 0; < cCrucibleOutpostMax) {{
        id = xsArrayGetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + d);

        if (id >= 0) {{
            n++;
        }}
    }}

    if (n == 0) {{
        return;
    }}

    xsArrayResizeInt(crucibleOutpostIds, n);
    n = 0;

    for (d = 0; < cCrucibleOutpostMax) {{
        id = xsArrayGetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + d);

        if (id >= 0) {{
            xsArraySetInt(crucibleOutpostIds, n, id);
            n++;
        }}
    }}

    xsTaskUnits(crucibleOutpostIds, cActionTypeAttackMove, at);
}}

void crucibleOutpostSpawn(int o = 0) {{
    int slot = xsArrayGetInt(crucibleOutpostMain, xsArrayGetInt(crucibleOutpostArchetype, o));
    int unit = -1;
    int id = -1;
    int k = 0;
    int t = o * cCrucibleOutpostTiles + xsArrayGetInt(crucibleOutpostSpawned, o) % cCrucibleOutpostTiles;
    vector at = xsVectorSet(xsArrayGetFloat(crucibleOutpostTileX, t), xsArrayGetFloat(crucibleOutpostTileY, t), 0.0);

    if (xsGetRandomNumberLH(0, 100) >= {table.MAIN_SHARE}) {{
        slot = 1 - slot;
    }}

    unit = crucibleOutpostUnit(o, slot);

    if (unit < 0) {{
        unit = crucibleOutpostUnit(o, 1 - slot);
    }}

    for (d = 0; < cCrucibleOutpostMax) {{
        k = o * cCrucibleOutpostMax + d;

        if (xsArrayGetInt(crucibleOutpostDefenders, k) < 0) {{
            id = xsCreateUnit(unit, {LEGION}, at, false, false, false);
            xsArraySetInt(crucibleOutpostDefenders, k, id);
            xsArraySetFloat(crucibleOutpostDefenderHp, k, crucibleOutpostHp(id));
            xsArraySetInt(crucibleOutpostSpawned, o, xsArrayGetInt(crucibleOutpostSpawned, o) + 1);
            return;
        }}
    }}
}}

void crucibleOutpostSay(int o = 0, string what = "") {{
    string name = xsArrayGetString(crucibleOutpostName, o);
    string kind = xsArrayGetString(crucibleOutpostArchetypeName, xsArrayGetInt(crucibleOutpostArchetype, o));

    xsChatData(name + " (" + kind + "): " + what + ", level %d", crucibleOutpostLevel(o));
}}

void crucibleOutpostTurn(int o = 0) {{
    bool turtled = crucibleOutpostTurtled(o);
    int spawn = 0;

    if (turtled) {{
        xsArraySetInt(crucibleOutpostGrowth, o, xsArrayGetInt(crucibleOutpostGrowth, o) + {GROW_HARASSED});
    }} else {{
        xsArraySetInt(crucibleOutpostGrowth, o, xsArrayGetInt(crucibleOutpostGrowth, o) + {GROW});
        spawn = crucibleOutpostTarget(o) - crucibleOutpostCount(o);

        if (spawn > {SPAWN_PER_TICK}) {{
            spawn = {SPAWN_PER_TICK};
        }}

        for (n = 0; < spawn) {{
            crucibleOutpostSpawn(o);
        }}
    }}

    crucibleOutpostSend(o, crucibleOutpostHome(o));

    if (cCrucibleOutpostDebug) {{
        if (turtled) {{
            crucibleOutpostSay(o, "turtled, " + crucibleOutpostCount(o) + " defenders");
        }} else {{
            crucibleOutpostSay(o, "+" + spawn + " defenders, " + crucibleOutpostCount(o) + " in all");
        }}
    }}
}}

// One second of outpost `o`: its buildings' and defenders' HP (harassed?), destroyed?, its turn.
void crucibleOutpostWatch(int o = 0) {{
    int now = xsGetTime();
    float total = 0.0;
    float hp = 0.0;
    int id = -1;
    int k = 0;
    bool hit = false;
    vector at = cInvalidVector;

    for (b = xsArrayGetInt(crucibleOutpostBuildingStart, o); < xsArrayGetInt(crucibleOutpostBuildingStart, o + 1)) {{
        id = xsArrayGetInt(crucibleOutpostBuildings, b);
        hp = crucibleOutpostHp(id);
        total = total + hp;

        if (hp < xsArrayGetFloat(crucibleOutpostBuildingHp, b) - 0.5) {{
            hit = true;
            at = xsGetUnitPosition(id);
        }}

        xsArraySetFloat(crucibleOutpostBuildingHp, b, hp);
    }}

    if (total <= 0.0) {{
        xsArraySetInt(crucibleOutpostAlive, o, 0);

        if (cCrucibleOutpostDebug) {{
            crucibleOutpostSay(o, "destroyed, no more turns");
        }}

        return;
    }}

    for (d = 0; < cCrucibleOutpostMax) {{
        k = o * cCrucibleOutpostMax + d;
        id = xsArrayGetInt(crucibleOutpostDefenders, k);

        if (id < 0) {{
            continue;
        }}

        hp = crucibleOutpostHp(id);

        if (hp < xsArrayGetFloat(crucibleOutpostDefenderHp, k) - 0.5) {{
            hit = true;

            if (hp > 0.0) {{
                at = xsGetUnitPosition(id);
            }}
        }}

        if (hp <= 0.0) {{
            xsArraySetInt(crucibleOutpostDefenders, k, -1);
        }}

        xsArraySetFloat(crucibleOutpostDefenderHp, k, hp);
    }}

    if (hit) {{
        if (cCrucibleOutpostDebug && (crucibleOutpostTurtled(o) == false)) {{
            crucibleOutpostSay(o, "harassed, turtles");
        }}

        xsArraySetInt(crucibleOutpostHarassedAt, o, now);

        if (xsVectorGetX(at) < 0.0) {{
            at = crucibleOutpostHome(o);
        }}

        crucibleOutpostSend(o, at);
    }}

    if (now >= xsArrayGetInt(crucibleOutpostNextTurn, o)) {{
        xsArraySetInt(crucibleOutpostNextTurn, o, now + {TICK} + xsGetRandomNumberLH(0, {TICK_SPREAD}));
        crucibleOutpostTurn(o);
    }}
}}

rule crucibleOutpostStart
    active
    minInterval 1
{{
    if (xsGetTime() < {START_AT}) {{
        return;
    }}

{nl.join(setup)}
    crucibleOutpostBuildingHp = xsArrayCreateFloat({len(buildings)}, 0.0, "crucibleOutpostBuildingHp");
    crucibleOutpostArchetype = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostArchetype");
    crucibleOutpostGrowth = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostGrowth");
    crucibleOutpostAlive = xsArrayCreateInt(cCrucibleOutposts, 1, "crucibleOutpostAlive");
    crucibleOutpostNextTurn = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostNextTurn");
    crucibleOutpostHarassedAt = xsArrayCreateInt(cCrucibleOutposts, -1, "crucibleOutpostHarassedAt");
    crucibleOutpostSpawned = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostSpawned");
    crucibleOutpostDefenders = xsArrayCreateInt(cCrucibleOutposts * cCrucibleOutpostMax, -1,
        "crucibleOutpostDefenders");
    crucibleOutpostDefenderHp = xsArrayCreateFloat(cCrucibleOutposts * cCrucibleOutpostMax, 0.0,
        "crucibleOutpostDefenderHp");
    crucibleOutpostIds = xsArrayCreateInt(1, -1, "crucibleOutpostIds");

    for (b = 0; < {len(buildings)}) {{
        xsArraySetFloat(crucibleOutpostBuildingHp, b, crucibleOutpostHp(xsArrayGetInt(crucibleOutpostBuildings, b)));
    }}

    for (o = 0; < cCrucibleOutposts) {{
        xsArraySetInt(crucibleOutpostArchetype, o, xsGetRandomNumberLH(0, {len(table.ARCHETYPES)}));
        xsArraySetInt(crucibleOutpostNextTurn, o, {FIRST_TICK} + xsGetRandomNumberLH(0, {TICK_SPREAD // 2}));

        for (n = 0; < {START_DEFENDERS}) {{
            crucibleOutpostSpawn(o);
        }}

        if (cCrucibleOutpostDebug) {{
            crucibleOutpostSay(o, "starts with " + crucibleOutpostCount(o) + " defenders");
        }}
    }}

    xsEnableRule("crucibleOutposts");
    xsDisableSelf();
}}

rule crucibleOutposts
    inactive
    minInterval 1
{{
    for (o = 0; < cCrucibleOutposts) {{
        if (xsArrayGetInt(crucibleOutpostAlive, o) == 1) {{
            crucibleOutpostWatch(o);
        }}
    }}
}}
"""


def add(ctx, s) -> None:
    """The outposts' XS; call after waves.add (its XS comes first)."""
    ctx.xs(xs(s))
