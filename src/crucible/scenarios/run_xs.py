"""The XS crucible_run starts with: the Allies' walls randomly damaged, none destroyed (walls handed to the player and
all towers start whole, playtests 2026-11-21 and 22), the City States made invulnerable.
It runs once, at START: after the meta upgrades have taken the player's buildings back. (The Allies' other buildings in
the camp are destroyed then too: run.py.)

A roll between `low` and `high` is `low + xsGetRandomNumberLH(0, high - low + 1)`: RoR's xsGetRandomNumberLH(low, high)
returned 0 to high - low, not low to high (towers rolled 40-75% came out 4-34%, playtest 2026-11-21).
"""

START = 3  # seconds: after the kept buildings, towers and walls are made anew (about 1-2 s)

# how a wall starts: (chance in percent, lowest and highest HP in percent of its full HP); none destroyed (playtest
# 2026-11-21: the old 15% destroyed shared out among the rest)
WALL_STATES = (
    (53, 10, 35),  # heavily damaged
    (29, 40, 75),  # damaged
    (18, 80, 100),  # fine
)


def roll(low: int, high: int) -> str:
    """XS for a random int from `low` to `high`, both included."""
    return f"({low} + xsGetRandomNumberLH(0, {high - low + 1}))"


def _wall_rolls() -> str:
    rolls, total = [], 0

    for chance, low, high in WALL_STATES:
        total += chance
        rolls.append(f"if (roll < {total}) {{ percent = {roll(low, high)}; }}")

    return "\n        else ".join(rolls)


def start(
    walls: dict[int, int],
    city_states: list[int],
    *,
    allies: int,
    player: int,
    invulnerable: int,
) -> str:
    """`walls`: type -> its full HP."""
    wall_calls = "\n".join(
        f"    crucibleRunWalls({allies}, {unit}, {hp});" for unit, hp in walls.items()  # the player's start whole
    )
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
{invulnerable_calls}
    xsDisableSelf();
}}
"""
