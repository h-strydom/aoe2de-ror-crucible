"""Rules of crucible_run beyond the factions and waves (docs/arena.md):

- the Allies' towers are the tier the player has unlocked: Watch Towers for now (meta upgrades will raise it); the
  camp's Fortified Walls stay Fortified (the Walls upgrade hands over only the Small Walls);
- the player's tech tree: the Stone Age and part of the Tool Age (ALLOWED), no techs but Tool Age; meta upgrades
  unlock the rest (run_meta);
- the player never builds walls or gates (RoR's gates come with walls);
- the player gets City Watch for free at the start;
- Town Centers can be built from the Bronze Age (the data mod gives them a button: datamod.buildings);
- the Allies age up when the player does: their age tech upgrades their buildings' looks (run_xs keeps them at 1 HP);
- fish (not whales) hold twice their food: fishing ships don't move on to the next fish they can see.
"""

WATCH_TOWER, SENTRY_TOWER, GUARD_TOWER, BALLISTA_TOWER = 79, 234, 235, 236
TOWERS = (WATCH_TOWER, SENTRY_TOWER, GUARD_TOWER, BALLISTA_TOWER)
WALLS = (72, 117, 155)  # Small, Medium, Fortified Wall
WALL_TECHS = (11, 13, 14)  # Stone, Medium, Fortified Wall
GATE_CLASS = 39
CITY_WATCH = 128
TOWN_CENTER = 109
TOWN_CENTER_AGE = 2  # the Bronze Age: Town Centers can be built (playtest 2026-11-23)
AGES = ((1, 101), (2, 102), (3, 103))  # (current age the player reaches, the age tech): Tool, Bronze, Iron
CURRENT_AGE = 6  # resource
FISH_CLASSES = (5, 33)  # fish and shore fish; whales are class 63
TOOL_AGE = 101
VILLAGER_CLASS = 4  # the villager's job units (builder, farmer...) are trained "at" the Town Center: never off
ALLOWED = (  # what the player can build or train out of the box
    83, 293, 109, 70, 12, 281, 68, 562, 45, 13,  # Stone Age: villagers, Town Center, House, Barracks, Clubman,
    # Granary, Storage Pit, Dock, Fishing Boat
    6, 7, 87, 4, 101, 448, 539, 545, 17, 84, 50,  # Tool Age: Slinger, Archery Range, Bowman, Stable, Scout, Scout
    # Ship, Light Transport, Trade Boat, Market, Farm
)
NOT_LOCKED = (TOOL_AGE, CITY_WATCH)


def tool_age_techs(data, techs: list[int]) -> list[int]:
    """Those of `techs` that need the Tool Age (and no later age)."""
    return [tech for tech in techs if TOOL_AGE in data.techs[tech].required_techs]


def techs_at(data, building: int) -> list[int]:
    """The techs researched at `building` with a button (research time above 0: at 0 the game researches a tech by
    itself, as RoR's hidden enablers are)."""
    return [
        i
        for i, tech in enumerate(data.techs)
        if any(r.location_id == building and r.research_time > 0 for r in tech.research_locations)
    ]


def locked(data) -> tuple[list[int], list[int]]:
    """What the player can't build, train or research out of the box: (units, techs)."""
    units = data.civs[1].units
    trained = {
        i
        for i, u in enumerate(units)
        if u and u.creatable and any(c.unit_id >= 0 for c in u.creatable.train_locations)
    }
    off_units = sorted(i for i in trained if i not in ALLOWED and units[i].class_ != VILLAGER_CLASS)
    buildings = {i for i in trained if units[i].type == 80} | {TOWN_CENTER}
    off_techs = sorted(
        {tech for building in buildings for tech in techs_at(data, building) if tech not in NOT_LOCKED}
    )

    return off_units, off_techs


def tier_one_towers(s, allies: int) -> None:
    """The Allies' towers become Watch Towers. Their walls stay as placed (the Fortified Walls round the camp had gone
    in play once they were turned into Small Walls, 2026-11-21)."""
    for unit in s.unit_manager.units[allies]:
        if unit.unit_const in TOWERS:
            unit.unit_const = WATCH_TOWER


def gates(data) -> list[int]:
    """The gates a player can build: RoR's stone and city gates."""
    return [i for i, u in enumerate(data.civs[1].units) if u and u.type == 80 and u.class_ == GATE_CLASS and u.enabled]


def add(ctx, *, player: int, allies: int, gates: list[int], locked: tuple[list[int], list[int]]) -> None:
    """`locked`: locked(data)."""
    units, techs = locked
    ctx.trigger(
        "Player: the Crucible's tech tree",
        [],
        [
            *(
                {"type": "enable_disable_object", "source_player": player, "object_list_unit_id": u, "enabled": 0}
                for u in units
            ),
            *(
                {"type": "enable_disable_technology", "source_player": player, "technology": t, "enabled": 0}
                for t in techs
            ),
        ],
    )
    off = [
        *(
            {"type": "enable_disable_object", "source_player": player, "object_list_unit_id": unit, "enabled": 0}
            for unit in (*WALLS, *gates)
        ),
        *(
            {"type": "enable_disable_technology", "source_player": player, "technology": tech, "enabled": 0}
            for tech in WALL_TECHS
        ),
    ]
    ctx.trigger("Player: no walls or gates", [], off)
    ctx.trigger(
        "Player: free City Watch",
        [],
        [
            {
                "type": "research_technology",
                "source_player": player,
                "technology": CITY_WATCH,
                "force_research_technology": 1,
            }
        ],
    )

    ctx.trigger(
        "Player: Town Centers from the Bronze Age",
        [
            {
                "type": "accumulate_attribute",
                "source_player": player,
                "attribute": CURRENT_AGE,
                "quantity": TOWN_CENTER_AGE,
            }
        ],
        [{"type": "enable_disable_object", "source_player": player, "object_list_unit_id": TOWN_CENTER, "enabled": 1}],
    )

    for age, tech in AGES:
        research = {"type": "research_technology", "source_player": allies, "technology": tech}
        ctx.trigger(
            f"Allies: age {age}",
            [{"type": "accumulate_attribute", "source_player": player, "attribute": CURRENT_AGE, "quantity": age}],
            [research | {"force_research_technology": 1}],
        )


def fish_xs(fish: list[int]) -> str:
    calls = "\n".join(f"    crucibleRunDoubleFish({unit});" for unit in fish)

    return f"""// ---- crucible run: fish hold twice their food ----
void crucibleRunDoubleFish(int type = -1) {{
    int ids = xsGetPlayerUnitIds(0, type, -1);
    int id = -1;

    for (i = 0; < xsArrayGetSize(ids)) {{
        id = xsArrayGetInt(ids, i);
        xsSetUnitProperty(id, cUnitAttributeHeld, 2 * xsGetUnitProperty(id, cUnitAttributeHeld));
    }}
}}

rule crucibleRunFish
    active
    highFrequency
{{
{calls}
    xsDisableSelf();
}}
"""
