"""Ruins and artifacts in the run (playtest 2026-11-23, docs/arena.md).

The arena has 7 Artifact Ruins and 5 artifacts. The Wonder's Ruins and Artifacts upgrades keep one of each a level,
picked at random each run (XS), and remove the rest. Ruins are captured on contact; artifacts too, as the data mod's
garrisonable copy (ARTIFACT_KEY, placed with capture flag 2), which the player garrisons in a building: 1 artifact
boosts every building of that type (STRUCTURES).

What they do is bought at the hub's towers, a stage a tower (meta: RUIN_TRICKLE... ARTIFACT_SPECIAL):
- ruins: a trickle of each resource, then population room, then population limit, each per ruin held;
- artifacts: the building type works faster (work rate), then its units and techs cost less, then a Granary trickles
  food, a Storage Pit wood, a Town Center gold and stone (per building, capped), and towers regenerate.

An artifact another player captures goes back to Gaia (a looping trigger): the player couldn't capture one back from the
Legion (playtest 2026-11-24).

Each artifact garrisoned counts: two in Barracks boost Barracks twice (a second did nothing, playtest 2026-11-24). The
bounty stage also makes the units the building type trains regenerate (ARTIFACT_UNIT_REGENERATION a minute an
artifact: an artifact in a Barracks, infantry; a Dock, ships; a Stable, cavalry; playtest 2026-11-24). The artifact
regenerates (ARTIFACT_CART_REGENERATION) wherever it is. Regeneration values are what shows a minute; the attribute
gets 1 / REGENERATION_SHOWN of it.
The Trade Workshop's Tribute: the Wonder trickles each resource while it stands (WONDER_TRICKLE_RATE a level).

Verified in game (2026-11-23): ruins pay; an artifact garrisons, and boosts and discounts a Town Center and a
Barracks. The cap (resource 32) and the room (resource 4) from
XS too (2026-11-24). Unverified: the towers' regeneration.
"""

from crucible import meta
from crucible.scenarios.run_rules import TOWERS, techs_at

RUIN, ARTIFACT = 52, 25
ARTIFACT_KEY = "artifact"  # the data mod's garrisonable artifact
GAIA = 0
CAPTURE_MULTIPLE = 2  # capture flag: captured on contact, again and again (a placed copy acts like a real artifact)
TOWER = "Tower"
STRUCTURES = {  # a building type -> its first building (the rest of its age chain counts too)
    "Town Center": meta.TOWN_CENTER,
    "Granary": meta.GRANARY,
    "Storage Pit": meta.STORAGE_PIT,
    "Barracks": meta.BARRACKS,
    "Archery Range": meta.ARCHERY_RANGE,
    "Stable": meta.STABLE,
    "Academy": meta.ACADEMY,
    "Siege Workshop": meta.SIEGE_WORKSHOP,
    "Temple": meta.TEMPLE,
    "Dock": meta.DOCK,
    "Market": meta.MARKET,
    "Government Center": meta.GOVERNMENT_CENTER,
}
WORK_RATE = 13
COSTS = (103, 104, 105, 106)  # food, wood, gold, stone cost (unit attributes)
REGENERATION = 109
WONDER = 276
POPULATION_ROOM, POPULATION_LIMIT = 4, 32  # player resources
RESOURCES = {"food": 0, "wood": 1, "stone": 2, "gold": 3}
PLAYER_CIV = 1


def groups(data) -> dict[str, tuple[int, ...]]:
    """Each building type's units: its look in every age (age chains), the towers' line."""
    from crucible.scenarios.run_meta import _chain, age_chains

    chains = age_chains(data)
    found = {name: tuple(sorted(_chain(chains, first))) for name, first in STRUCTURES.items()}
    found[TOWER] = TOWERS

    return found


def trained(data, buildings: tuple[int, ...]) -> list[int]:
    """The units trained at `buildings` (a tower's own type: built, not trained, so it's its own)."""
    units = data.civs[PLAYER_CIV].units
    found = [
        i
        for i, u in enumerate(units)
        if u and u.creatable and any(c.unit_id in buildings for c in u.creatable.train_locations)
    ]

    return found or list(buildings)


def _int_array(name: str, values: list[int]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateInt({max(len(values), 1)}, -1, "{name}");']

    return lines + [f"    xsArraySetInt({name}, {n}, {v});" for n, v in enumerate(values)]


def _apply(name: str, g: int, ids: tuple[int, ...], data, stages: dict[str, str], player: int) -> list[str]:
    """XS: the stages of group `g` on (`on`) or off, each a factor and its inverse."""
    lines = [f"    if (kind == {g}) {{"]

    if name != TOWER:
        lines.append(f"        if ({stages['speed']} > 0) {{")
        lines += [
            f"            xsEffectAmount(cMulAttribute, {i}, {WORK_RATE}, crucibleRelicFactor(on, speed), {player});"
            for i in ids
        ]
        lines.append("        }")

    lines.append(f"        if ({stages['cost']} > 0) {{")
    lines += [
        f"            xsEffectAmount(cMulAttribute, {u}, {cost}, crucibleRelicFactor(on, cost), {player});"
        for u in trained(data, ids)
        for cost in COSTS
    ]
    techs = sorted({t for b in ids for t in techs_at(data, b)})
    lines += [
        f"            xsEffectAmount(cModifyTech, {t}, cAttrMulAllCosts, crucibleRelicFactor(on, cost), {player});"
        for t in techs
    ]
    lines.append("        }")

    regenerating = ids if name == TOWER else [u for u in trained(data, ids) if u not in ids]
    shown = meta.ARTIFACT_REGENERATION if name == TOWER else meta.ARTIFACT_UNIT_REGENERATION

    if regenerating:
        lines.append(f"        if ({stages['special']} > 0) {{")
        lines += [
            f"            xsEffectAmount(cAddAttribute, {i}, {REGENERATION}, crucibleRelicSign(on) * "
            f"{shown / meta.REGENERATION_SHOWN}, {player});"
            for i in regenerating
        ]
        lines.append("        }")

    return lines + ["    }"]


def xs(ctx, data, player: int, ruins: list[int], artifacts: list[int], artifact: int) -> str:
    """`ruins` and `artifacts`: the trigger variable ids that remove each; `artifact`: the copy's unit type."""
    from crucible.scenarios.run_meta import _variable_id

    def level(upgrade: meta.Upgrade) -> str:
        return f"xsTriggerVariable({_variable_id(ctx, upgrade.key)})"

    stages = {
        "speed": level(meta.ARTIFACT_SPEED),
        "cost": level(meta.ARTIFACT_COST),
        "special": level(meta.ARTIFACT_SPECIAL),
    }
    found = groups(data)
    names = list(found)
    apply = [line for g, name in enumerate(names) for line in _apply(name, g, found[name], data, stages, player)]
    trickles = []

    for name, payouts in meta.ARTIFACT_TRICKLES.items():
        g = names.index(name)
        count = " + ".join(f"xsGetObjectCount({player}, {i})" for i in found[name])
        trickles.append(f"    if (xsArrayGetInt(crucibleRelicApplied, {g}) >= 1) {{")
        trickles.append(f"        count = {count};")
        trickles.append(f"        times = xsArrayGetInt(crucibleRelicApplied, {g});")
        trickles += [
            f"        crucibleRelicAdd({RESOURCES[resource]}, crucibleRelicMin(count * {each}, {most}) * times);"
            for resource, each, most in payouts
        ]
        trickles.append("    }")

    scans = []

    for g, name in enumerate(names):
        for i in found[name]:
            scans += [
                f"    crucibleRelicBuildings = xsGetPlayerUnitIds({player}, {i}, crucibleRelicBuildings);",
                f"    crucibleRelicMatch({g}, garrisoned);",
            ]

    name_sets = [f'    xsArraySetString(crucibleRelicNames, {g}, "{name}");' for g, name in enumerate(names)]
    cart = meta.ARTIFACT_CART_REGENERATION / meta.REGENERATION_SHOWN
    speed = 1 + meta.ARTIFACT_SPEED_PERCENT / 100
    cost = 1 - meta.ARTIFACT_DISCOUNT_PERCENT / 100
    nl = "\n"

    return f"""// ---- crucible run: ruins and artifacts ----
int crucibleRelicIds = -1;  // reused: the player's artifacts
int crucibleRelicHeld = -1;  // building type -> artifacts garrisoned in its buildings
int crucibleRelicApplied = -1;  // building type -> times its stages are on (an artifact each)
int crucibleRelicBuildings = -1;  // reused: the player's buildings of one type
int crucibleRelicNames = -1;  // building type -> its name, for the chat
int crucibleRelicContainers = -1;  // the buildings the player's artifacts are garrisoned in
int crucibleRelicSeen = -1;  // artifacts held and garrisoned, last said in the chat (as held * 100 + garrisoned)
int crucibleRelicRoom = 0;  // population room given so far
int crucibleRelicLimit = 0;  // population limit given so far
const float cCrucibleRelicSpeed = {speed};
const float cCrucibleRelicCost = {cost};

float crucibleRelicFactor(bool on = false, float factor = 1.0) {{
    if (on) {{
        return (factor);
    }}

    return (1.0 / factor);
}}

float crucibleRelicSign(bool on = false) {{
    if (on) {{
        return (1.0);
    }}

    return (-1.0);
}}

float crucibleRelicMin(float a = 0.0, float b = 0.0) {{
    if (a < b) {{
        return (a);
    }}

    return (b);
}}

void crucibleRelicAdd(int resource = 0, float amount = 0.0) {{
    xsSetPlayerAttribute({player}, resource, xsPlayerAttribute({player}, resource) + amount);
}}

// Keep `keep` of `count` at random: each of the rest gets its removal variable (vars) set to 1.
void crucibleRelicPick(int vars = -1, int count = 0, int keep = 0) {{
    int kept = 0;

    for (i = 0; < count) {{
        if (xsGetRandomNumberLH(0, count - i) < keep - kept) {{
            kept++;
        }} else {{
            xsSetTriggerVariable(xsArrayGetInt(vars, i), 1);
        }}
    }}
}}

// Building type `kind` holds an artifact for each of the `count` containers that is one of its buildings (the list).
// Matched by unit id: xsGetUnitType on the container didn't give a building type (playtest 2026-11-23).
void crucibleRelicMatch(int kind = -1, int count = 0) {{
    for (b = 0; < xsArrayGetSize(crucibleRelicBuildings)) {{
        for (c = 0; < count) {{
            if (xsArrayGetInt(crucibleRelicBuildings, b) == xsArrayGetInt(crucibleRelicContainers, c)) {{
                xsArraySetInt(crucibleRelicHeld, kind, xsArrayGetInt(crucibleRelicHeld, kind) + 1);
            }}
        }}
    }}
}}

void crucibleRelicScan(int garrisoned = 0) {{
{nl.join(scans)}
}}

void crucibleRelicApply(int kind = -1, bool on = false) {{
    float speed = cCrucibleRelicSpeed;
    float cost = cCrucibleRelicCost;
{nl.join(apply)}
}}

rule crucibleRelicStart
    active
    minInterval 1
{{
    if (xsGetTime() < 2) {{
        return;  // after the bank's load
    }}

    int ruins = -1;
    int artifacts = -1;
{nl.join(_int_array("ruins", ruins))}
{nl.join(_int_array("artifacts", artifacts))}
    crucibleRelicPick(ruins, {len(ruins)}, {level(meta.RUINS)});
    crucibleRelicPick(artifacts, {len(artifacts)}, {level(meta.ARTIFACTS)});
    crucibleRelicHeld = xsArrayCreateInt({len(names)}, 0, "crucibleRelicHeld");
    crucibleRelicApplied = xsArrayCreateInt({len(names)}, 0, "crucibleRelicApplied");
    crucibleRelicContainers = xsArrayCreateInt({meta.ARTIFACT_SPOTS}, -1, "crucibleRelicContainers");
    crucibleRelicNames = xsArrayCreateString({len(names)}, "", "crucibleRelicNames");
{nl.join(name_sets)}
    xsEffectAmount(cAddAttribute, {artifact}, {REGENERATION}, {cart}, {player});
    xsEffectAmount(cAddAttribute, {artifact}, {REGENERATION}, {cart}, {GAIA});
    xsEnableRule("crucibleRelics");
    xsDisableSelf();
}}

rule crucibleRelics
    inactive
    minInterval 1
{{
    int ruins = xsGetObjectCount({player}, {RUIN});
    int room = 0;
    int limit = 0;
    int container = -1;
    int count = 0;
    int held = 0;
    int garrisoned = 0;
    int times = 0;

    if ({level(meta.RUIN_TRICKLE)} > 0) {{
        for (r = 0; < 4) {{
            crucibleRelicAdd(r, {meta.RUIN_TRICKLE_RATE} * ruins);
        }}
    }}

    if (({level(meta.WONDER_TRICKLE)} > 0) && (xsGetObjectCount({player}, {WONDER}) > 0)) {{
        for (w = 0; < 4) {{
            crucibleRelicAdd(w, {meta.WONDER_TRICKLE_RATE} * {level(meta.WONDER_TRICKLE)});
        }}
    }}

    if ({level(meta.RUIN_ROOM)} > 0) {{
        room = ruins * {meta.RUIN_ROOM_EACH};
        crucibleRelicAdd({POPULATION_ROOM}, room - crucibleRelicRoom);
        crucibleRelicRoom = room;
    }}

    if ({level(meta.RUIN_CAP)} > 0) {{
        limit = ruins * {meta.RUIN_CAP_EACH};
        crucibleRelicAdd({POPULATION_LIMIT}, limit - crucibleRelicLimit);
        crucibleRelicLimit = limit;
    }}

    for (g = 0; < {len(names)}) {{
        xsArraySetInt(crucibleRelicHeld, g, 0);
    }}

    crucibleRelicIds = xsGetPlayerUnitIds({player}, {artifact}, crucibleRelicIds);
    held = xsArrayGetSize(crucibleRelicIds);

    for (a = 0; < held) {{
        container = xsGetGarrisonedInUnitId(xsArrayGetInt(crucibleRelicIds, a));

        if ((container >= 0) && (garrisoned < {meta.ARTIFACT_SPOTS})) {{
            xsArraySetInt(crucibleRelicContainers, garrisoned, container);
            garrisoned++;
        }}
    }}

    if (garrisoned > 0) {{
        crucibleRelicScan(garrisoned);
    }}

    if (held * 100 + garrisoned != crucibleRelicSeen) {{
        crucibleRelicSeen = held * 100 + garrisoned;
        xsChatData("Artifacts held: %d", held);
        xsChatData("Artifacts found garrisoned: %d", garrisoned);
    }}

    for (h = 0; < {len(names)}) {{
        if (xsArrayGetInt(crucibleRelicHeld, h) != xsArrayGetInt(crucibleRelicApplied, h)) {{
            xsChatData("Artifact: " + xsArrayGetString(crucibleRelicNames, h) + " boosted by %d",
                xsArrayGetInt(crucibleRelicHeld, h));
        }}

        while (xsArrayGetInt(crucibleRelicApplied, h) < xsArrayGetInt(crucibleRelicHeld, h)) {{
            crucibleRelicApply(h, true);
            xsArraySetInt(crucibleRelicApplied, h, xsArrayGetInt(crucibleRelicApplied, h) + 1);
        }}

        while (xsArrayGetInt(crucibleRelicApplied, h) > xsArrayGetInt(crucibleRelicHeld, h)) {{
            crucibleRelicApply(h, false);
            xsArraySetInt(crucibleRelicApplied, h, xsArrayGetInt(crucibleRelicApplied, h) - 1);
        }}
    }}

    if ({stages["special"]} > 0) {{
{nl.join("    " + line for line in trickles)}
    }}
}}
"""


def add(ctx, s, data, techs: dict[str, int], player: int, others: tuple[int, ...]) -> None:
    """The map's ruins and artifacts (Gaia's): artifacts become the garrisonable copy; each gets a trigger that removes
    it once XS sets its variable; then the XS."""
    from crucible.scenarios.run_meta import _variable_id

    gaia = s.unit_manager.units[GAIA]
    ruins = [u for u in gaia if u.unit_const == RUIN]
    artifacts = [u for u in gaia if u.unit_const == ARTIFACT]
    assert (len(ruins), len(artifacts)) == (meta.RUIN_SPOTS, meta.ARTIFACT_SPOTS), (len(ruins), len(artifacts))
    copy = techs[ARTIFACT_KEY]

    for unit in artifacts:
        unit.unit_const = copy
        unit.capture_flag = CAPTURE_MULTIPLE

    for other in others:
        ctx.trigger(
            f"Relics: player {other}'s artifacts back to Gaia",
            [{"type": "own_objects", "source_player": other, "object_list": copy, "quantity": 1}],
            [
                {
                    "type": "change_ownership",
                    "source_player": other,
                    "target_player": GAIA,
                    "object_list_unit_id": copy,
                }
            ],
            looping=True,
        )

    variables = {}

    for kind, units in (("ruin", ruins), ("artifact", artifacts)):
        variables[kind] = []

        for n, unit in enumerate(units):
            name = f"crucible_{kind}_{n}"
            variables[kind].append(_variable_id(ctx, name))
            ctx.trigger(
                f"Relics: {kind} {n} not this run",
                [{"type": "variable_value", "variable": name, "comparison": "EQUAL", "quantity": 1}],
                [{"type": "remove_object", "source_player": GAIA, "selected_object_ids": [unit.reference_id]}],
            )

    ctx.xs(xs(ctx, data, player, variables["ruin"], variables["artifact"], copy))
