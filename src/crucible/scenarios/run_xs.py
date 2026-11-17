"""The XS crucible_run starts with: the Allies' buildings to 1 HP, their walls randomly damaged, the City States made
invulnerable. It runs once, on the first tick.
"""

# how a wall starts: (chance in percent, lowest and highest HP in percent of its full HP); more damaged than destroyed
# or whole
WALL_STATES = (
    (15, 0, 0),  # destroyed
    (45, 10, 35),  # heavily damaged
    (25, 40, 75),  # damaged
    (15, 80, 100),  # fine
)


def _wall_rolls() -> str:
    rolls, total = [], 0

    for chance, low, high in WALL_STATES:
        total += chance
        rolls.append(f"if (roll < {total}) {{ percent = xsGetRandomNumberLH({low}, {high + 1}); }}")

    return "\n        else ".join(rolls)


def start(
    walls: dict[int, int],
    buildings: list[int],
    city_states: list[int],
    *,
    allies: int,
    invulnerable: int,
) -> str:
    """`walls`: wall type -> its full HP."""
    wall_calls = "\n".join(f"    crucibleRunWalls({unit}, {hp});" for unit, hp in walls.items())
    building_calls = "\n".join(f"    crucibleRunOneHp({unit});" for unit in buildings)
    invulnerable_calls = "\n".join(f"    crucibleRunInvulnerable({unit});" for unit in city_states)

    return f"""// ---- crucible run: start ----
void crucibleRunWalls(int type = -1, int hp = 0) {{
    int ids = xsGetPlayerUnitIds({allies}, type, -1);
    int id = -1;
    int roll = 0;
    int percent = 0;

    for (i = 0; < xsArrayGetSize(ids)) {{
        id = xsArrayGetInt(ids, i);
        roll = xsGetRandomNumberLH(0, 100);
        {_wall_rolls()}
        xsSetUnitProperty(id, cUnitHitpoints, hp * percent / 100);
    }}
}}

void crucibleRunOneHp(int type = -1) {{
    int ids = xsGetPlayerUnitIds({allies}, type, -1);
    int id = -1;

    for (i = 0; < xsArrayGetSize(ids)) {{
        id = xsArrayGetInt(ids, i);
        xsEffectAmount(cSetUnitAttribute, id, cHitpoints, 1, {allies});
        xsSetUnitProperty(id, cUnitHitpoints, 1);
    }}
}}

void crucibleRunInvulnerable(int type = -1) {{
    int ids = xsGetPlayerUnitIds({invulnerable}, type, -1);
    // splash hits a unit whose blast defence level is at least the attack's (catapults 2, buildings 2-3, units 3):
    // at 0, like trees, nothing but a level 0 attack splashes it
    xsEffectAmount(cSetAttribute, type, cBlastDefenseLevel, 0, {invulnerable});

    for (i = 0; < xsArrayGetSize(ids)) {{
        xsSetUnitProperty(xsArrayGetInt(ids, i), cUnitAttackable, 0);
    }}
}}

rule crucibleRunStart
    active
    highFrequency
{{
{wall_calls}
{building_calls}
{invulnerable_calls}
    xsDisableSelf();
}}
"""
