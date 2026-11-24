"""The Legion's outposts come alive (docs/outposts.md): defend, guard their spots, attack.

Each of the six bases (`bases.BASES`) rolls an archetype at the start, as a wave lane does (`wave_table.ARCHETYPES`),
and fields its paths' lines up to the Legion's age (`crucibleWaveAge`, from waves.xs): a higher level fields later
lines. Outposts never roll upgrades of their own; the Legion's are shared, so they have the waves'.

What an outpost does is XS (outposts.xs, read it for the detail); this module works out the map's part of it, from
the markers placed on the arena (player 4's, 2026-11-24; the run takes them off the map and keeps their tiles):
- Priests: where an outpost's garrison stands about, each unit wandering round one or patrolling between two;
- Scouts: the spots it guards (resources); a spot with more resources gets more guards (`SPOT_EACH`); a spot belongs
  to the nearest outpost its units can walk to;
- Fishing Boats: where a sea outpost's ships keep;
- Kings: where a sea outpost's transports land their waves, the 3 nearest it (one at random a wave).
Units come out of the outpost's buildings (a free tile by each: `doors`), ships out of its docks; a building
destroyed spawns nothing more, so with its docks gone a sea outpost has no more ships.
The Legion's own markers stay as they were: its female villagers on the south edge, where land outposts' waves come
from, and its Light Transports on the map's edge, where a sea outpost's transports (and their escorts) come from and
go back to; a trigger removes them there (`exits`).

Playtest 2026-11-24 (standard): the aggression felt right for Hard, so Moderate and Standard scale it down
(AGGRESSION); the garrison is 2, 4 and 6 times the first test's (GARRISON_SCALE), twice that while turtled.
Second playtest (Hard): turtling for 5 minutes was too long (2 now), turns too slow (TURN_SPEED), no raids, spots
with 1 or 2 guards at 45 minutes, the first land attack at 15 minutes. Now everything grows with time
(TimeGrowth: parties, waves, turns, turtled top-ups) and with each outpost destroyed (FallenBonus, and the
survivors gain levels); raids hunt the player's villagers outside their base; a spot the player is on gets a
party at once; attack waves are twice as big and come from FIRST_WAVE on; units swap to a better line at once.
"""

import math
from collections import deque
from functools import cache
from pathlib import Path

from crucible.datamod.mod import source_dat
from crucible.scenarios import bases
from crucible.scenarios import wave_table as table

RUNTIME = Path(__file__).with_name("outposts.xs")
LEGION, PLAYER, MARKERS = 3, 1, 4
LAND_MARKER = 293  # the Legion's female villager: a land outpost's waves start here
SEA_MARKER = 545  # the Legion's Light Transport: a sea outpost's transports start (and leave) here
SHIP_SPOT, POST, LANDING, GUARD_SPOT = 13, 125, 434, 448  # player 4's Fishing Boat, Priest, King, Scout
MARKER_TYPES = (SHIP_SPOT, POST, LANDING, GUARD_SPOT)
WONDER = 276
SEA_OUTPOSTS = ("Western Outpost", "Eastern Outpost")

DEBUG = True  # chat says what each outpost does: for the playtests only (outposts are meant to be silent)
NUMBERS = {  # the XS constants (cCrucibleOutpost + the name)
    "Start": 10,  # seconds: the first look (after waves.xs has set up)
    "FirstTick": 60,  # seconds: the first turn (+ up to half TickSpread)
    "Tick": 90,  # seconds between turns, + 0 to TickSpread, divided by TURN_SPEED and the power
    "TickSpread": 60,
    "Turtle": 120,  # seconds after the last harassment an outpost stays turtled (300 was too long)
    "TimeGrowth": 3,  # percent more power a minute: parties, waves, turns and turtled top-ups
    "TimeMax": 400,
    "FallenBonus": 25,  # percent more power for each outpost destroyed
    "FallenGrowth": 20,  # growth points (2 levels) each surviving outpost gains when one is destroyed
    "Grow": 10,  # growth points a turn left alone (10 a level)
    "GrowHarassed": 3,  # turtled
    "StartDefenders": 3,  # the garrison's base: + a level's and an age's worth, times GARRISON_SCALE
    "LevelsPerDefender": 2,
    "DefendersPerAge": 2,
    "Max": 120,  # land units in a garrison at most
    "ShipMax": 40,
    "Members": 220,  # units an outpost keeps track of: garrison, spot guards, ships
    "SpawnPerTick": 3,  # more of the garrison a turn, times the power (12 replenished too fast, 2026-11-24)
    "TurtleSpawnEvery": 30,  # seconds: turtled and left alone, it tops up this often (less with the power)
    "TurtleSpawn": 3,
    "LevelsPerLine": 4,  # a level step of this many moves its units a line on
    "MainShare": table.MAIN_SHARE,
    "BullyBase": 2,  # a party sent to a contested spot: + BullyPer a pressure, + the Legion's age
    "BullyPer": 2,
    "BullyMax": 20,
    "BullyEvery": 45,  # seconds between parties to a spot the player stays on (less with the power)
    "SpotMax": 30,  # guards at one spot at most
    "SpotLow": 75,  # percent: a spot with fewer guards than this of what it wants is refilled
    "Refills": 2,  # spots refilled a turn at most
    "RaidBase": 3,  # a raid: + RaidPerAge an age (times the aggression and the power)
    "RaidPerAge": 2,
    "RaidMax": 16,
    "PressureEvery": 30,  # seconds: a spot's pressure goes up while contested, down while clear
    "PressureMax": 10,
    "WaveBase": 3,  # an attack wave: + a level / 2, + 2 an age, times WaveScale (and the aggression, the power)
    "WaveScale": 2,  # twice the first tests' (playtest 2026-11-24)
    "WaveMax": 60,
    "WaveOverdue": 300,  # seconds: a wave comes even while spots are being refilled (less with the power)
    "TransportMax": 8,
    "LightTransport": 545,
    "HeavyTransport": 37,
    "LightCapacity": 5,
    "HeavyCapacity": 10,
    "EscortPer": 6,  # an escort ship for every this many in a wave, + 1
    "EscortMax": 4,
    "Escorts": 16,  # escorts out at once at most
    "LandTimeout": 150,  # seconds: a transport lands by then wherever it is; then it's forgotten
    "ScanEvery": 2,  # seconds between looks at the player's units (and new orders)
    "EnemyMax": 400,
    "WanderEvery": 6,  # seconds between a wanderer's steps, + 0 to WanderSpread
    "WanderSpread": 8,
    "PatrolEvery": 3,  # every this many garrison units, one patrols between two posts
}
RANGES = {  # tiles (floats in XS)
    "HuntRange": 25.0,  # the player's units this near an outpost stop its spawning, and turtled it hunts them
    "SpotRadius": 8.0,  # the player's units this near a spot contest it
    "SeaRange": 60.0,  # ships go for the player's ships and docks this near their outpost
    "PostWander": 3.0,  # how far a garrison unit wanders from its post
    "SpotWander": 4.0,  # a spot guard from its spot
    "ShipWander": 4.0,  # a ship from its spot
    "Landed": 4.0,  # a transport this near its landing lands its party
    "RaidSafe": 22.0,  # the player's villagers this near the Wonder are in their base: never raided
    "RaidReach": 110.0,  # an outpost raids villagers this near it
    "RaidChase": 15.0,  # raiders go for villagers this near where they were sent, else home
}
GARRISON_SCALE = (2, 4, 6)  # by difficulty (Standard, Moderate, Hard): the garrison, its base times this
TURTLE_SCALE = (4, 8, 12)  # while turtled
AGGRESSION = (50, 75, 100)  # percent: parties, raids and waves this size
TURN_SPEED = (75, 100, 160)  # percent: turns this much more often (Hard's were too slow, playtest 2026-11-24)
FIRST_WAVE = (900, 750, 600)  # seconds: no attack wave before (Hard's first came at 15 minutes)
RAID_SHARE = (25, 35, 50)  # percent of turns that send a raid
KINGS_PER_SIDE = 3
SPOT_EACH = 1000  # a spot's resources: a guard each this many (SPOT_GUARDS), + the Legion's age
SPOT_GUARDS = (3, 8)  # 1 or 2 guards at 45 minutes was too few (playtest 2026-11-24)
SPOT_REACH = 7  # tiles round a scout whose resources count
SEA_SPAWN = 3  # tiles in from a sea marker (on the map's edge) its transports start at; they leave at the marker
EXIT = 1  # tiles round a sea marker a trigger removes the Legion's transports and escorts in
AGES = len(table.Age)
SLOTS = (table.Slot.MELEE, table.Slot.RANGED)
LAND_CLASSES = (0, 4, 6, 12, 13, 18, 23, 24, 35, 36, 44, 47, 55)  # what the outposts hunt on land
VILLAGER_CLASS = 4
SEA_CLASSES = (2, 20, 21, 22)  # trade boats, transports, fishing boats, warships
DOCKS = (45, 133, 47, 51)
SHIP_LINES = ((539, table.Age.STONE), (21, table.Age.BRONZE), (442, table.Age.IRON), (420, table.Age.IRON))
CLUBMAN, SCOUT_SHIP = 281, 539  # whose terrain restrictions say where land units walk and ships sail
BUILDING = 80


@cache
def _data():
    """The game's data (parsed once: it takes seconds)."""
    return source_dat()


@cache
def walkable() -> frozenset[int]:
    """The terrains land units walk on (RoR's shallows and beaches too)."""
    return _passable(CLUBMAN)


@cache
def sailable() -> frozenset[int]:
    """The terrains ships sail on (shallows and beaches too: docks stand on shallows)."""
    return _passable(SCOUT_SHIP)


def _passable(unit: int) -> frozenset[int]:
    data = _data()
    restriction = data.terrain_restrictions[data.civs[PLAYER].units[unit].terrain_restriction]

    return frozenset(t for t, value in enumerate(restriction.passable_buildable_dmg_multiplier) if value > 0)


def take(s) -> dict[str, list[tuple[float, float]]]:
    """Remove the markers from scenario `s`; returns their tiles by kind: land, sea (the Legion's), posts, spots,
    ship_spots, landings (player 4's)."""
    kinds = {
        LEGION: {LAND_MARKER: "land", SEA_MARKER: "sea"},
        MARKERS: {POST: "posts", GUARD_SPOT: "spots", SHIP_SPOT: "ship_spots", LANDING: "landings"},
    }
    found = {kind: [] for by_type in kinds.values() for kind in by_type.values()}
    markers = []

    for player, by_type in kinds.items():
        for unit in s.unit_manager.units[player]:
            kind = by_type.get(unit.unit_const)

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


def ship_types() -> list[int]:
    """Every ship an outpost fields, and its transports."""
    return sorted({unit for unit, _ in SHIP_LINES} | {NUMBERS["LightTransport"], NUMBERS["HeavyTransport"]})


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
    """Every unit's tile and how far to keep clear of it (buildings by their size)."""
    data = _data().civs[1].units
    taken = []

    for player in s.unit_manager.units:
        for u in player:
            unit = data[u.unit_const] if u.unit_const < len(data) else None
            taken.append((u.x, u.y, _size(unit) + 0.5 if unit and unit.type == BUILDING else 1.0))

    return taken


def _size(unit) -> float:
    return max(unit.clearance_size[0], unit.clearance_size[1], 0.5)


def _around(s, x: float, y: float, near: int):
    size = s.map_manager.map_size

    for tx in range(max(0, int(x) - near), min(size, int(x) + near + 1)):
        for ty in range(max(0, int(y) - near), min(size, int(y) + near + 1)):
            yield tx, ty


def door(s, building, taken, dock: bool) -> tuple[float, float] | None:
    """A free tile by `building` its units come out at (water by a dock); None if there's none."""
    data = _data().civs[1].units
    mm = s.map_manager
    reach = _size(data[building.unit_const]) + 3
    best = None

    for tx, ty in _around(s, building.x, building.y, math.ceil(reach)):
        centre = (tx + 0.5, ty + 0.5)
        d = math.dist(centre, (building.x, building.y))
        terrain = mm.get_tile(tx, ty).terrain_id

        if d > reach or terrain not in (sailable() if dock else walkable()):
            continue

        if all(math.dist(centre, (ux, uy)) > r for ux, uy, r in taken) and (best is None or d < best[0]):
            best = (d, centre)

    return best[1] if best else None


def regions(s) -> list[list[int]]:
    """Each tile's region (tiles a land unit can walk between), -1 where it can't walk; [x][y]."""
    mm = s.map_manager
    size = mm.map_size
    region = [[-1] * size for _ in range(size)]
    count = 0

    for x in range(size):
        for y in range(size):
            if region[x][y] >= 0 or mm.get_tile(x, y).terrain_id not in walkable():
                continue

            region[x][y] = count
            queue = deque([(x, y)])

            while queue:
                cx, cy = queue.popleft()

                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    inside = 0 <= nx < size and 0 <= ny < size

                    if inside and region[nx][ny] < 0 and mm.get_tile(nx, ny).terrain_id in walkable():
                        region[nx][ny] = count
                        queue.append((nx, ny))

            count += 1

    return region


def resources(s, at: tuple[float, float]) -> int:
    """The food, wood, stone and gold Gaia's units hold within SPOT_REACH of `at` (trees left out)."""
    data = _data().civs[0].units
    total = 0

    for u in s.unit_manager.units[0]:
        unit = data[u.unit_const] if u.unit_const < len(data) else None

        if unit and unit.class_ != 15 and math.dist((u.x, u.y), at) <= SPOT_REACH:  # 15: trees
            total += sum(r.amount for r in unit.resource_storages if r.type in (0, 1, 2, 3) and r.amount > 0)

    return int(total)


def _water_near(s, at: tuple[float, float]) -> tuple[float, float]:
    """The nearest tile only ships can use (open water) to `at`."""
    mm = s.map_manager
    water = sailable() - walkable()
    tiles = [t for t in _around(s, *at, 8) if mm.get_tile(*t).terrain_id in water]

    if not tiles:
        raise ValueError(f"no water near the landing at {at}")

    x, y = min(tiles, key=lambda t: math.dist((t[0] + 0.5, t[1] + 0.5), at))

    return x + 0.5, y + 0.5


def _inward(s, at: tuple[float, float], by: float) -> tuple[float, float]:
    """`by` tiles in from the map's edge nearest `at`."""
    size = s.map_manager.map_size
    x, y = at
    edges = {(by, 0.0): x, (-by, 0.0): size - x, (0.0, by): y, (0.0, -by): size - y}
    dx, dy = min(edges, key=edges.get)

    return x + dx, y + dy


def exits(s, sea: list[tuple[float, float]]) -> list[tuple[int, int, int, int]]:
    """The areas (x1, y1, x2, y2) round each sea marker where transports and escorts are removed."""
    size = s.map_manager.map_size
    clip = lambda v: max(0, min(size - 1, int(v)))  # noqa: E731

    return [(clip(x - EXIT), clip(y - EXIT), clip(x + EXIT), clip(y + EXIT)) for x, y in sea]


def plan(s, markers: dict[str, list[tuple[float, float]]]) -> dict[str, list]:
    """Each outpost's part of the map, by outpost; and the spots, the sea markers, the Wonder."""
    wonder = next((u.x, u.y) for u in s.unit_manager.units[PLAYER] if u.unit_const == WONDER)
    taken = _taken(s)
    region = regions(s)
    keys = ("home", "buildings", "doors", "posts", "ship_spots", "landings", "sea", "marker", "sea_markers")
    found = {key: [] for key in keys}
    homes = []

    for _, box in bases.BASES:
        built = bases.buildings(s, box)
        homes.append((sum(u.x for u in built) / len(built), sum(u.y for u in built) / len(built)))

    def nearest_outpost(at, among=None) -> int:
        among = range(len(homes)) if among is None else among
        return min(among, key=lambda o: math.dist(homes[o], at))

    sea_flags = [name in SEA_OUTPOSTS for name, _ in bases.BASES]
    sea_ones = [o for o, sea in enumerate(sea_flags) if sea]
    land_regions = []

    for o, (name, box) in enumerate(bases.BASES):
        built = bases.buildings(s, box)
        home = homes[o]
        doors = []

        for u in built:
            dock = u.unit_const in DOCKS
            at = door(s, u, taken, dock)

            if at:
                doors.append((u.reference_id, at, dock))

        land = [at for _, at, dock in doors if not dock]

        if not land:
            raise ValueError(f"{name}: no door for land units")

        land_regions.append(region[int(land[0][0])][int(land[0][1])])
        posts = [p for p in markers["posts"] if nearest_outpost(p) == o] or [home]
        ship_spots = [p for p in markers["ship_spots"] if nearest_outpost(p, sea_ones) == o] if sea_flags[o] else []
        kings = sorted(markers["landings"], key=lambda k: math.dist(k, home))[:KINGS_PER_SIDE]
        sea_markers = sorted(markers["sea"], key=lambda m: math.dist(m, home))[:2]
        found["home"].append(home)
        found["buildings"].append([u.reference_id for u in built])
        found["doors"].append(doors)
        found["posts"].append(posts)
        found["ship_spots"].append(ship_spots or [home])
        found["landings"].append([(k, _water_near(s, k)) for k in kings] if sea_flags[o] else [])
        found["sea"].append(sea_flags[o])
        found["marker"].append(min(markers["land"], key=lambda m: math.dist(m, home)))
        found["sea_markers"].append([(_inward(s, m, SEA_SPAWN), m) for m in sea_markers] if sea_flags[o] else [])

    spots = []

    for at in sorted(markers["spots"]):
        reachable = [o for o in range(len(homes)) if land_regions[o] == region[int(at[0])][int(at[1])]]
        owner = nearest_outpost(at, reachable) if reachable else -1
        guards = min(max(round(resources(s, at) / SPOT_EACH), SPOT_GUARDS[0]), SPOT_GUARDS[1])
        spots.append((at, owner, guards))

    found["spots"] = spots
    found["wonder"] = wonder

    return found


def _ints(name: str, values: list[int]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateInt({max(len(values), 1)}, -1, "{name}");']

    return lines + [f"    xsArraySetInt({name}, {n}, {v});" for n, v in enumerate(values)]


def _floats(name: str, values: list[float]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateFloat({max(len(values), 1)}, 0.0, "{name}");']

    return lines + [f"    xsArraySetFloat({name}, {n}, {float(v)});" for n, v in enumerate(values)]


def _strings(name: str, values: list[str]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateString({max(len(values), 1)}, "", "{name}");']

    return lines + [f'    xsArraySetString({name}, {n}, "{v}");' for n, v in enumerate(values)]


def _flat(per_outpost: list[list]) -> tuple[list[int], list]:
    """(each outpost's start in the flat list, + the end), the flat list."""
    starts, flat = [], []

    for items in per_outpost:
        starts.append(len(flat))
        flat += items

    return starts + [len(flat)], flat


def xs(s, markers: dict[str, list[tuple[float, float]]]) -> str:
    """The outposts' XS (after waves.xs: it reads crucibleWaveAge and crucibleWaveDifficulty). `markers`: take(s)."""
    p = plan(s, markers)
    land, sea = player_types(_data())
    building_start, buildings = _flat(p["buildings"])
    door_start, doors = _flat(p["doors"])
    post_start, posts = _flat(p["posts"])
    ship_spot_start, ship_spots = _flat(p["ship_spots"])
    landing_start, landings = _flat(p["landings"])
    sea_start, sea_markers = _flat(p["sea_markers"])
    pool_start, pool_units = _flat(pools())
    ship_start, ship_units = _flat(ship_pools())
    spots = p["spots"]
    setup = [
        *_floats("crucibleOutpostHomesX", [x for x, _ in p["home"]]),
        *_floats("crucibleOutpostHomesY", [y for _, y in p["home"]]),
        *_ints("crucibleOutpostBuildingStart", building_start),
        *_ints("crucibleOutpostBuildings", buildings),
        *_ints("crucibleOutpostDoorStart", door_start),
        *_ints("crucibleOutpostDoorBuilding", [ref for ref, _, _ in doors]),
        *_floats("crucibleOutpostDoorX", [at[0] for _, at, _ in doors]),
        *_floats("crucibleOutpostDoorY", [at[1] for _, at, _ in doors]),
        *_ints("crucibleOutpostDoorDock", [int(dock) for _, _, dock in doors]),
        *_ints("crucibleOutpostPostStart", post_start),
        *_floats("crucibleOutpostPostX", [x for x, _ in posts]),
        *_floats("crucibleOutpostPostY", [y for _, y in posts]),
        *_ints("crucibleOutpostShipSpotStart", ship_spot_start),
        *_floats("crucibleOutpostShipSpotX", [x for x, _ in ship_spots]),
        *_floats("crucibleOutpostShipSpotY", [y for _, y in ship_spots]),
        *_ints("crucibleOutpostLandingStart", landing_start),
        *_floats("crucibleOutpostLandingX", [k[0] for k, _ in landings]),
        *_floats("crucibleOutpostLandingY", [k[1] for k, _ in landings]),
        *_floats("crucibleOutpostLandingWaterX", [w[0] for _, w in landings]),
        *_floats("crucibleOutpostLandingWaterY", [w[1] for _, w in landings]),
        *_ints("crucibleOutpostSeaMarkerStart", sea_start),
        *_floats("crucibleOutpostSeaSpawnX", [spawn[0] for spawn, _ in sea_markers]),
        *_floats("crucibleOutpostSeaSpawnY", [spawn[1] for spawn, _ in sea_markers]),
        *_floats("crucibleOutpostSeaExitX", [m[0] for _, m in sea_markers]),
        *_floats("crucibleOutpostSeaExitY", [m[1] for _, m in sea_markers]),
        *_ints("crucibleOutpostIsSea", [int(at_sea) for at_sea in p["sea"]]),
        *_floats("crucibleOutpostMarkerX", [m[0] for m in p["marker"]]),
        *_floats("crucibleOutpostMarkerY", [m[1] for m in p["marker"]]),
        *_ints("crucibleOutpostPoolStart", pool_start),
        *_ints("crucibleOutpostPoolUnits", pool_units),
        *_ints("crucibleOutpostShipPoolStart", ship_start),
        *_ints("crucibleOutpostShipPoolUnits", ship_units),
        *_ints("crucibleOutpostMain", [int(a.main) for a in table.ARCHETYPES]),
        *_strings("crucibleOutpostName", [name for name, _ in bases.BASES]),
        *_strings("crucibleOutpostArchetypeName", [a.name for a in table.ARCHETYPES]),
        *_floats("crucibleOutpostSpotX", [at[0] for at, _, _ in spots]),
        *_floats("crucibleOutpostSpotY", [at[1] for at, _, _ in spots]),
        *_ints("crucibleOutpostSpotOwner", [owner for _, owner, _ in spots]),
        *_ints("crucibleOutpostSpotGuards", [guards for _, _, guards in spots]),
        *_strings("crucibleOutpostSpotName", [f"the spot at {int(at[0])}, {int(at[1])}" for at, _, _ in spots]),
        *_ints("crucibleOutpostLandTypes", [t for t, _ in land]),
        *_ints("crucibleOutpostLandVillager", [int(v) for _, v in land]),
        *_ints("crucibleOutpostSeaTypes", sea),
        *_ints("crucibleOutpostGarrisonScale", list(GARRISON_SCALE)),
        *_ints("crucibleOutpostTurtleScale", list(TURTLE_SCALE)),
        *_ints("crucibleOutpostAggression", list(AGGRESSION)),
        *_ints("crucibleOutpostTurnSpeed", list(TURN_SPEED)),
        *_ints("crucibleOutpostFirstWave", list(FIRST_WAVE)),
        *_ints("crucibleOutpostRaidShare", list(RAID_SHARE)),
    ]
    arrays = sorted({line.split(" = ")[0].strip() for line in setup if " = xsArrayCreate" in line})
    constants = [
        f"const int cCrucibleOutposts = {len(bases.BASES)};",
        f"const int cCrucibleOutpostSpots = {len(spots)};",
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
    """The outposts' XS, and the triggers that take their transports and escorts off the map at the sea markers they
    sail back to (XS can only kill a unit, and it showed sinking); call after waves.add (its XS comes first).
    `markers`: take(s), before anything else."""
    for n, area in enumerate(exits(s, markers["sea"])):
        for unit in ship_types():
            where = {"area": list(area)}
            ctx.trigger(
                f"Outposts: ship {unit} leaves at sea marker {n}",
                [{"type": "objects_in_area", "source_player": LEGION, "object_list": unit, "quantity": 1, **where}],
                [{"type": "remove_object", "source_player": LEGION, "object_list_unit_id": unit, **where}],
                looping=True,
            )

    ctx.xs(xs(s, markers))
