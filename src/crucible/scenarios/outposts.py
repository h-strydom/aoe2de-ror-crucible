"""The Legion's outposts come alive (docs/outposts.md): phases 2-4, defend, guard and bully, attack.

Each of the six bases (`bases.BASES`) rolls an archetype at the start, as a wave lane does (`wave_table.ARCHETYPES`),
and fields its paths' lines up to the Legion's age (`crucibleWaveAge`, from waves.xs): a higher level fields later
lines. Outposts never roll upgrades of their own; the Legion's are shared, so they have the waves'.

What an outpost does is XS (outposts.xs, read it for the detail); this module works out the map's part of it:
- its garrison's posts, spread through its base (POSTS: free tiles round each building in turn), and for the two sea
  outposts their ships' posts round the island (SEA_POSTS) and the beach their transports land waves on;
- the spots it guards (`spots`): gold and stone clusters of 4 or more mines, hunt groups of 3 or more, outside the
  player's base (BaseRadius round the Wonder), each the spot of every outpost within SPOT_RANGE;
- where its attack waves start: land outposts at the nearest land marker, sea outposts at their two nearest sea
  markers (by transport);
- the player's unit types the outposts look for (the map hack: `xsGetPlayerUnitIds` a type at a time).

Playtest 2026-11-24: garrisons 4 times as large (GarrisonScale) and spread through the base, 8 times while turtled
(TurtleScale); hit, the garrison hunts the player's units near the base (it had walked to where it was hit and back
until it died); sea outposts keep half the garrison as ships.

Markers (2026-11-23): the Legion's female villagers on land and its Light Transports at sea mark where the outposts'
attack waves come from; the run takes them off the map and keeps their tiles.
"""

import math
from pathlib import Path

from AoE2ScenarioParser.datasets.terrains import TerrainId

from crucible.datamod.mod import source_dat
from crucible.scenarios import bases
from crucible.scenarios import wave_table as table

RUNTIME = Path(__file__).with_name("outposts.xs")
LEGION, PLAYER = 3, 1
LAND_MARKER = 293  # VFBAS, the female villager
SEA_MARKER = 545  # Light Transport
WONDER = 276
SEA_OUTPOSTS = ("Western Outpost", "Eastern Outpost")

DEBUG = True  # chat says what each outpost does: for the playtests only (outposts are meant to be silent)
NUMBERS = {  # the XS constants (cCrucibleOutpost + the name)
    "Start": 10,  # seconds: the first look (after waves.xs has set up)
    "FirstTick": 60,  # seconds: the first turn (+ up to half TickSpread)
    "Tick": 120,  # seconds between turns, + 0 to TickSpread
    "TickSpread": 120,
    "Turtle": 180,  # seconds after the last harassment an outpost stays turtled
    "Grow": 10,  # growth points a turn left alone (10 a level)
    "GrowHarassed": 3,  # turtled
    "StartDefenders": 3,  # the garrison's base: + a level's, an age's and a difficulty step's worth
    "LevelsPerDefender": 2,
    "DefendersPerAge": 2,
    "DifficultyDefenders": 2,
    "GarrisonScale": 4,  # the garrison: its base times this (playtest 2026-11-24)
    "TurtleScale": 8,  # while turtled
    "Max": 120,  # land units in a garrison at most
    "ShipMax": 60,
    "SpawnPerTick": 12,  # more of the garrison a turn
    "TurtleSpawnEvery": 15,  # seconds: turtled, it tops up this often
    "TurtleSpawn": 4,
    "LevelsPerLine": 4,  # a level step of this many moves its units a line on
    "MainShare": table.MAIN_SHARE,
    "OutMax": 80,  # units out (guards, bullies, raiders) at most
    "GuardBase": 2,  # a guard or raiding party: + a level / 4, + the Legion's age
    "GuardMax": 8,
    "RaidMax": 10,
    "BullyBase": 2,  # a bullying party: + BullyPer a pressure, + the Legion's age
    "BullyPer": 2,
    "BullyMax": 16,
    "PressureEvery": 30,  # seconds: a spot's pressure goes up while contested, down while clear
    "PressureMax": 10,
    "WaveBase": 3,  # an attack wave: + a level / 2, + 2 an age, + 2 a difficulty step
    "WaveMax": 30,
    "TransportMax": 8,
    "LightTransport": 545,
    "HeavyTransport": 37,
    "LightCapacity": 5,
    "HeavyCapacity": 10,
    "LandTimeout": 150,  # seconds: a transport lands (or leaves) by then wherever it is
    "ScanEvery": 2,  # seconds between looks at the player's units
    "EnemyMax": 400,
}
RANGES = {  # tiles (floats in XS)
    "HuntRange": 25.0,  # turtled, the garrison hunts the player's units this near its base
    "SpotRadius": 8.0,  # the player's units this near a spot contest it
    "HelpRange": 60.0,  # parties help at spots and raid gatherers this near their base
    "BaseRadius": 30.0,  # the player's base: round the Wonder; gatherers outside it are raided
    "SeaRange": 60.0,  # ships go for the player's ships and docks this near their base
}
POSTS, SEA_POSTS = 16, 8
SPOT_RANGE = 50  # a spot belongs to every outpost this near
GOLD, STONE = 66, 102
HUNT_CLASSES, HUNT_EXTRA = (9,), (1301,)  # prey (gazelles, deer...) and elephants
MINES, HERD = 4, 3  # a spot's least mines or animals
LINK = {"gold": 3.0, "stone": 3.0, "hunt": 5.0}  # tiles: a cluster's members are this near one another
LAND_CLASSES = (0, 4, 6, 12, 13, 18, 23, 24, 35, 36, 44, 47, 55)  # what the outposts hunt and harass on land
VILLAGER_CLASS = 4
SEA_CLASSES = (2, 20, 21, 22)  # trade boats, transports, fishing boats, warships
DOCKS = (45, 133, 47, 51)
SHIP_LINES = ((539, table.Age.STONE), (21, table.Age.BRONZE), (442, table.Age.IRON), (420, table.Age.IRON))
AGES = len(table.Age)
SLOTS = (table.Slot.MELEE, table.Slot.RANGED)
WATER = {t.value for t in TerrainId if "WATER" in t.name and "BRIDGE" not in t.name}
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


def ship_pools() -> list[list[int]]:
    """By age: the ships a sea outpost fields, later is better."""
    return [[unit for unit, at in SHIP_LINES if at <= age] for age in table.Age]


def player_types(data) -> tuple[list[tuple[int, bool]], list[int]]:
    """The unit types the player may have that outposts look for: (land: (type, a villager?)), sea (ships, docks)."""
    units = data.civs[PLAYER].units
    land, sea = [], list(DOCKS)

    for i, u in enumerate(units):
        if not (u and u.type == 70 and u.creatable) or u.name.startswith("Hero"):
            continue

        trained = any(c.unit_id >= 0 for c in u.creatable.train_locations)

        if not trained and u.class_ != VILLAGER_CLASS:  # every villager's job, female ones aren't trained
            continue

        if u.class_ in LAND_CLASSES:
            land.append((i, u.class_ == VILLAGER_CLASS))
        elif u.class_ in SEA_CLASSES:
            sea.append(i)

    return land, sea


def _taken(s) -> list[tuple[float, float, float]]:
    """Every unit's tile and how far to keep clear of it (buildings wider)."""
    data = source_dat().civs[1].units
    taken = []

    for player in s.unit_manager.units:
        for u in player:
            unit = data[u.unit_const] if u.unit_const < len(data) else None
            taken.append((u.x, u.y, 2.5 if unit and unit.type == BUILDING else 1.2))

    return taken


def _free(s, taken, x: int, y: int) -> bool:
    if s.map_manager.get_tile(x, y).terrain_id in BLOCKED:
        return False

    return all(math.dist((x + 0.5, y + 0.5), (ux, uy)) > r for ux, uy, r in taken)


def _around(s, x: float, y: float, near: int):
    size = s.map_manager.map_size

    for tx in range(max(0, int(x) - near), min(size, int(x) + near + 1)):
        for ty in range(max(0, int(y) - near), min(size, int(y) + near + 1)):
            yield tx, ty


def posts(s, found: list, count: int = POSTS, taken=None) -> list[tuple[float, float]]:
    """Free land tiles spread through a base: the nearest free tile to each of its buildings in turn, 2 tiles apart."""
    taken = _taken(s) if taken is None else taken
    near = {}

    for b in found:
        tiles = [t for t in _around(s, b.x, b.y, 5) if _free(s, taken, *t)]
        near[b.reference_id] = sorted(tiles, key=lambda t: math.dist((t[0] + 0.5, t[1] + 0.5), (b.x, b.y)))

    chosen = []

    while len(chosen) < count:
        added = False

        for b in found:
            for t in near[b.reference_id]:
                if all(math.dist(t, c) >= 2 for c in chosen):
                    chosen.append(t)
                    added = True
                    break

            if len(chosen) == count:
                break

        if not added:
            raise ValueError(f"only {len(chosen)} posts round {[b.reference_id for b in found]}")

    return [(x + 0.5, y + 0.5) for x, y in chosen]


def sea_posts(s, home: tuple[float, float], count: int = SEA_POSTS) -> list[tuple[float, float]]:
    """Water tiles round an island outpost, 6 to 16 tiles out, 4 apart: where its ships keep."""
    mm = s.map_manager
    tiles = [
        t
        for t in _around(s, *home, 16)
        if mm.get_tile(*t).terrain_id in WATER and 6 <= math.dist((t[0] + 0.5, t[1] + 0.5), home) <= 16
    ]
    tiles.sort(key=lambda t: math.dist((t[0] + 0.5, t[1] + 0.5), home))
    chosen = []

    for t in tiles:
        if all(math.dist(t, c) >= 4 for c in chosen):
            chosen.append(t)

        if len(chosen) == count:
            return [(x + 0.5, y + 0.5) for x, y in chosen]

    raise ValueError(f"only {len(chosen)} sea posts round {home}")


def beach(s, home: tuple[float, float], wonder: tuple[float, float], taken=None) -> tuple[tuple, tuple]:
    """Where a sea outpost's transports land: a free shore tile 10 to 30 tiles from it, the nearest the Wonder; (the
    land tile, the water tile off it)."""
    mm = s.map_manager
    taken = _taken(s) if taken is None else taken
    size = mm.map_size
    best = None

    for x, y in _around(s, *home, 30):
        if not 10 <= math.dist((x + 0.5, y + 0.5), home) <= 30 or not _free(s, taken, x, y):
            continue

        for wx, wy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= wx < size and 0 <= wy < size and mm.get_tile(wx, wy).terrain_id in WATER:
                d = math.dist((x, y), wonder)

                if best is None or d < best[0]:
                    best = (d, (x + 0.5, y + 0.5), (wx + 0.5, wy + 0.5))

    if best is None:
        raise ValueError(f"no beach near {home}")

    return best[1], best[2]


def _clusters(points: list[tuple[float, float]], link: float) -> list[list[tuple[float, float]]]:
    groups = []

    for p in points:
        joined = [g for g in groups if any(math.dist(p, q) <= link for q in g)]
        merged = [p, *(q for g in joined for q in g)]
        groups = [g for g in groups if g not in joined] + [merged]

    return groups


def spots(s, wonder: tuple[float, float]) -> list[tuple[str, float, float]]:
    """The resource spots outposts guard: (kind, x, y), outside the player's base."""
    data = source_dat().civs[0].units
    kinds = {"gold": [], "stone": [], "hunt": []}

    for u in s.unit_manager.units[0]:
        unit = data[u.unit_const] if u.unit_const < len(data) else None

        if u.unit_const == GOLD:
            kinds["gold"].append((u.x, u.y))
        elif u.unit_const == STONE:
            kinds["stone"].append((u.x, u.y))
        elif u.unit_const in HUNT_EXTRA or (unit and unit.class_ in HUNT_CLASSES):
            kinds["hunt"].append((u.x, u.y))

    found = []

    for kind, points in kinds.items():
        least = HERD if kind == "hunt" else MINES

        for group in _clusters(points, LINK[kind]):
            x, y = sum(p[0] for p in group) / len(group), sum(p[1] for p in group) / len(group)

            if len(group) >= least and math.dist((x, y), wonder) > RANGES["BaseRadius"]:
                found.append((kind, round(x, 1), round(y, 1)))

    return sorted(found, key=lambda f: (f[1], f[2]))


def _ints(name: str, values: list[int]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateInt({max(len(values), 1)}, -1, "{name}");']

    return lines + [f"    xsArraySetInt({name}, {n}, {v});" for n, v in enumerate(values)]


def _floats(name: str, values: list[float]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateFloat({max(len(values), 1)}, 0.0, "{name}");']

    return lines + [f"    xsArraySetFloat({name}, {n}, {float(v)});" for n, v in enumerate(values)]


def _strings(name: str, values: list[str]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateString({max(len(values), 1)}, "", "{name}");']

    return lines + [f'    xsArraySetString({name}, {n}, "{v}");' for n, v in enumerate(values)]


def plan(s, markers: dict[str, list[tuple[float, float]]]) -> dict[str, list]:
    """Each outpost's part of the map, by outpost: home, buildings, posts, sea posts, sea?, markers, beach, spots."""
    wonder = next((u.x, u.y) for u in s.unit_manager.units[PLAYER] if u.unit_const == WONDER)
    taken = _taken(s)
    every = spots(s, wonder)
    found = {key: [] for key in ("home", "buildings", "posts", "sea_posts", "sea", "markers", "beach", "spots")}

    for name, box in bases.BASES:
        built = bases.buildings(s, box)
        home = (sum(u.x for u in built) / len(built), sum(u.y for u in built) / len(built))
        sea = name in SEA_OUTPOSTS
        nearest = sorted(markers["sea" if sea else "land"], key=lambda m: math.dist(m, home))
        found["home"].append(home)
        found["buildings"].append([u.reference_id for u in built])
        found["posts"].append(posts(s, built, taken=taken))
        found["sea_posts"].append(sea_posts(s, home) if sea else [home] * SEA_POSTS)
        found["sea"].append(sea)
        found["markers"].append((nearest[0], nearest[1] if sea else nearest[0]))
        found["beach"].append(beach(s, home, wonder, taken) if sea else (home, home))
        found["spots"].append([n for n, (_, x, y) in enumerate(every) if math.dist((x, y), home) <= SPOT_RANGE])

    found["every_spot"] = every
    found["wonder"] = wonder

    return found


def xs(s, markers: dict[str, list[tuple[float, float]]]) -> str:
    """The outposts' XS (after waves.xs: it reads crucibleWaveAge and crucibleWaveFactor). `markers`: take(s)."""
    p = plan(s, markers)
    land, sea = player_types(source_dat())
    starts, buildings = [], []

    for found in p["buildings"]:
        starts.append(len(buildings))
        buildings += found

    starts.append(len(buildings))
    pool_start, pool_units = [], []

    for units in pools():
        pool_start.append(len(pool_units))
        pool_units += units

    pool_start.append(len(pool_units))
    ship_start, ship_units = [], []

    for units in ship_pools():
        ship_start.append(len(ship_units))
        ship_units += units

    ship_start.append(len(ship_units))
    spot_start, own = [], []

    for found in p["spots"]:
        spot_start.append(len(own))
        own += found

    spot_start.append(len(own))
    every = p["every_spot"]
    flat = [post for found in p["posts"] for post in found]
    sea_flat = [post for found in p["sea_posts"] for post in found]
    setup = [
        *_floats("crucibleOutpostHomesX", [x for x, _ in p["home"]]),
        *_floats("crucibleOutpostHomesY", [y for _, y in p["home"]]),
        *_ints("crucibleOutpostBuildingStart", starts),
        *_ints("crucibleOutpostBuildings", buildings),
        *_floats("crucibleOutpostPostX", [x for x, _ in flat]),
        *_floats("crucibleOutpostPostY", [y for _, y in flat]),
        *_floats("crucibleOutpostSeaPostX", [x for x, _ in sea_flat]),
        *_floats("crucibleOutpostSeaPostY", [y for _, y in sea_flat]),
        *_ints("crucibleOutpostIsSea", [int(at_sea) for at_sea in p["sea"]]),
        *_floats("crucibleOutpostMarkerX", [m[0][0] for m in p["markers"]]),
        *_floats("crucibleOutpostMarkerY", [m[0][1] for m in p["markers"]]),
        *_floats("crucibleOutpostMarker2X", [m[1][0] for m in p["markers"]]),
        *_floats("crucibleOutpostMarker2Y", [m[1][1] for m in p["markers"]]),
        *_floats("crucibleOutpostBeachX", [b[0][0] for b in p["beach"]]),
        *_floats("crucibleOutpostBeachY", [b[0][1] for b in p["beach"]]),
        *_floats("crucibleOutpostBeachWaterX", [b[1][0] for b in p["beach"]]),
        *_floats("crucibleOutpostBeachWaterY", [b[1][1] for b in p["beach"]]),
        *_ints("crucibleOutpostPoolStart", pool_start),
        *_ints("crucibleOutpostPoolUnits", pool_units),
        *_ints("crucibleOutpostShipPoolStart", ship_start),
        *_ints("crucibleOutpostShipPoolUnits", ship_units),
        *_ints("crucibleOutpostMain", [int(a.main) for a in table.ARCHETYPES]),
        *_strings("crucibleOutpostName", [name for name, _ in bases.BASES]),
        *_strings("crucibleOutpostArchetypeName", [a.name for a in table.ARCHETYPES]),
        *_floats("crucibleOutpostSpotX", [x for _, x, _ in every]),
        *_floats("crucibleOutpostSpotY", [y for _, _, y in every]),
        *_strings("crucibleOutpostSpotName", [f"the {kind} at {int(x)}, {int(y)}" for kind, x, y in every]),
        *_ints("crucibleOutpostSpotStart", spot_start),
        *_ints("crucibleOutpostOwnSpots", own),
        *_ints("crucibleOutpostLandTypes", [t for t, _ in land]),
        *_ints("crucibleOutpostLandVillager", [int(v) for _, v in land]),
        *_ints("crucibleOutpostSeaTypes", sea),
    ]
    arrays = sorted({line.split(" = ")[0].strip() for line in setup if " = xsArrayCreate" in line})
    constants = [
        f"const int cCrucibleOutposts = {len(bases.BASES)};",
        f"const int cCrucibleOutpostPosts = {POSTS};",
        f"const int cCrucibleOutpostSeaPosts = {SEA_POSTS};",
        f"const int cCrucibleOutpostSpots = {len(every)};",
        f"const int cCrucibleOutpostAges = {AGES};",
        f"const int cCrucibleOutpostArchetypes = {len(table.ARCHETYPES)};",
        f"const int cCrucibleOutpostLegion = {LEGION};",
        f"const int cCrucibleOutpostPlayer = {PLAYER};",
        f"const bool cCrucibleOutpostDebug = {'true' if DEBUG else 'false'};",
        f"const float cCrucibleOutpostWonderX = {float(p['wonder'][0])};",
        f"const float cCrucibleOutpostWonderY = {float(p['wonder'][1])};",
        *(f"const int cCrucibleOutpost{name} = {value};" for name, value in NUMBERS.items()),
        *(f"const float cCrucibleOutpost{name} = {value};" for name, value in RANGES.items()),
    ]
    nl = "\n"
    header = f"""// ---- crucible run: the Legion's outposts, data (generated: scenarios/outposts.py) ----
{nl.join(constants)}
{nl.join(f"int {name} = -1;" for name in arrays)}

void crucibleOutpostData() {{
{nl.join(setup)}
}}
"""

    return header + "\n" + RUNTIME.read_text(encoding="utf-8")


def add(ctx, s, markers: dict[str, list[tuple[float, float]]]) -> None:
    """The outposts' XS; call after waves.add (its XS comes first). `markers`: take(s), before anything else."""
    ctx.xs(xs(s, markers))
