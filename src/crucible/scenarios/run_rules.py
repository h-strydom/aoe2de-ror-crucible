"""Rules of crucible_run beyond the factions and waves (docs/arena.md):

- the Allies' towers are the tier the player has unlocked: Watch Towers for now (meta upgrades will raise it);
- the player never builds walls (RoR has no gates); towers only come from meta upgrades, so none for now either;
- the player gets City Watch for free at the start;
- the Allies age up when the player does: their age tech upgrades their buildings' looks (run_xs keeps them at 1 HP);
- fish (not whales) hold twice their food: fishing ships don't move on to the next fish they can see.
"""

WATCH_TOWER, SENTRY_TOWER, GUARD_TOWER, BALLISTA_TOWER = 79, 234, 235, 236
TOWERS = (WATCH_TOWER, SENTRY_TOWER, GUARD_TOWER, BALLISTA_TOWER)
SMALL_WALL = 72
WALL_AND_TOWER_TECHS = (11, 13, 14, 16, 12, 15, 2)  # Stone/Medium/Fortified Wall; Watch/Sentry/Guard/Catapult Tower
CITY_WATCH = 128
AGES = ((1, 101), (2, 102), (3, 103))  # (current age the player reaches, the age tech): Tool, Bronze, Iron
CURRENT_AGE = 6  # resource
FISH_CLASSES = (5, 33)  # fish and shore fish; whales are class 63


def tier_one_towers(s, allies: int) -> None:
    """The Allies' towers become Watch Towers."""
    for unit in s.unit_manager.units[allies]:
        if unit.unit_const in TOWERS:
            unit.unit_const = WATCH_TOWER


def add(ctx, *, player: int, allies: int) -> None:
    off = [
        *(
            {"type": "enable_disable_object", "source_player": player, "object_list_unit_id": unit, "enabled": 0}
            for unit in (SMALL_WALL, *TOWERS)
        ),
        *(
            {"type": "enable_disable_technology", "source_player": player, "technology": tech, "enabled": 0}
            for tech in WALL_AND_TOWER_TECHS
        ),
    ]
    ctx.trigger("Player: no walls or towers", [], off)
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
