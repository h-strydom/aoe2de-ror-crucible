"""The XS crucible_run starts with: the Allies' buildings to 1 HP, the base's walls randomly damaged (the Allies', or
the player's with the Walls upgrade), the City States made
invulnerable. It runs once, at 2 seconds: after the meta upgrades have taken the player's buildings back.
"""

START = 2  # seconds

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
    player: int,
    invulnerable: int,
    aged: list[int] = (),
) -> str:
    """`walls`: wall type -> its full HP. `aged`: the buildings' types in every age (their maximum HP is 1 for the
    Allies, so an age up keeps them at 1)."""
    wall_calls = "\n".join(
        f"    crucibleRunWalls({owner}, {unit}, {hp});" for owner in (allies, player) for unit, hp in walls.items()
    )
    max_calls = "\n".join(f"    crucibleRunMaxOneHp({unit});" for unit in sorted({*buildings, *aged}))
    building_calls = "\n".join(f"    crucibleRunOneHp({unit});" for unit in buildings)
    invulnerable_calls = "\n".join(f"    crucibleRunInvulnerable({unit});" for unit in city_states)

    return f"""// ---- crucible run: start ----
void crucibleRunWalls(int owner = -1, int type = -1, int hp = 0) {{
    int ids = xsGetPlayerUnitIds(owner, type, -1);
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

// The Allies' buildings at 1 HP: the type's maximum for the Allies (a per-unit maximum seemed to keep a building from
// taking its next age's look), in every age, so an age up keeps them at 1; then each one's current HP.
void crucibleRunMaxOneHp(int type = -1) {{
    xsEffectAmount(cSetAttribute, type, cHitpoints, 1, {allies});
}}

void crucibleRunOneHp(int type = -1) {{
    int ids = xsGetPlayerUnitIds({allies}, type, -1);

    for (i = 0; < xsArrayGetSize(ids)) {{
        xsSetUnitProperty(xsArrayGetInt(ids, i), cUnitHitpoints, 1);
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
    if (xsGetTime() < {START}) {{
        return;
    }}

{wall_calls}
{max_calls}
{building_calls}
{invulnerable_calls}
    xsDisableSelf();
}}
"""
