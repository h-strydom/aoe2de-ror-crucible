"""The XS crucible_run starts with: the base's walls and towers randomly damaged (the Allies', or the player's with
the Walls or Watch Tower upgrade), the City States made invulnerable. It runs once, at START: after the meta upgrades
have taken the player's buildings back. (The Allies' other buildings are removed then too: run.py.)
"""

TOWER_LOG_EVERY, TOWER_LOGS = 30, 6  # TEMPORARY: tower HP in chat every 30 s for 3 minutes
TOWER_HP = (40, 75)  # a tower starts between these, in percent of its full HP (10-50 was too low, 2026-11-21)

START = 3  # seconds: after the kept buildings, towers and walls are made anew (about 1-2 s)

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
    towers: dict[int, int],
    city_states: list[int],
    *,
    allies: int,
    player: int,
    invulnerable: int,
) -> str:
    """`walls`, `towers`: type -> its full HP."""
    wall_calls = "\n".join(
        f"    crucibleRunWalls({owner}, {unit}, {hp});" for owner in (allies, player) for unit, hp in walls.items()
    )
    tower_calls = "\n".join(
        f"    crucibleRunTowers({owner}, {unit}, {hp});" for owner in (allies, player) for unit, hp in towers.items()
    )
    invulnerable_calls = "\n".join(f"    crucibleRunInvulnerable({unit});" for unit in city_states)
    log_calls = "\n".join(
        f"    text = text + crucibleRunTowerHp({owner}, {unit});" for owner in (allies, player) for unit in towers
    )

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

void crucibleRunTowers(int owner = -1, int type = -1, int hp = 0) {{
    int ids = xsGetPlayerUnitIds(owner, type, -1);
    int percent = 0;

    for (i = 0; < xsArrayGetSize(ids)) {{
        percent = xsGetRandomNumberLH({TOWER_HP[0]}, {TOWER_HP[1] + 1});
        xsSetUnitProperty(xsArrayGetInt(ids, i), cUnitHitpoints, hp * percent / 100);
    }}
}}

// TEMPORARY (towers ended up far below the roll, 2026-11-21): each tower's HP and its type's full HP, in chat.
string crucibleRunTowerHp(int owner = -1, int type = -1) {{
    int ids = xsGetPlayerUnitIds(owner, type, -1);
    string text = "";
    int hp = 0;

    for (i = 0; < xsArrayGetSize(ids)) {{
        hp = xsGetUnitHitpoints(xsArrayGetInt(ids, i));
        text = text + " p" + owner + ":" + hp;
    }}

    if (xsArrayGetSize(ids) > 0) {{
        int full = xsGetObjectAttribute(owner, type, cHitpoints, 0);
        text = text + " (full " + full + ")";
    }}

    return (text);
}}

void crucibleRunTowerLog(string when = "") {{
    string text = "Towers " + when + ":";
{log_calls}
    xsChatData(text);
}}

int crucibleRunTowerLogs = 0;

rule crucibleRunTowerWatch
    inactive
    minInterval {TOWER_LOG_EVERY}
{{
    crucibleRunTowerLogs++;
    crucibleRunTowerLog("at " + xsGetTime() + " s");

    if (crucibleRunTowerLogs >= {TOWER_LOGS}) {{
        xsDisableSelf();
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
{tower_calls}
{invulnerable_calls}
    crucibleRunTowerLog("rolled");
    xsEnableRule("crucibleRunTowerWatch");
    xsDisableSelf();
}}
"""
