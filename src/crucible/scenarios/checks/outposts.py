"""Test: how the sea outposts (docs/outposts.md) land a wave from a transport.

Confirmed 2026-11-23, so gone from here:
- XS reads a building's HP (`xsGetUnitProperty(id, cUnitHitpoints)`);
- loading works both ways: XS setting `cUnitGarrisonedInId` on units made on land, and the trigger "Create Garrisoned
  Object" (transport type in an area);
- no transport landed when told to (trigger Unload or Task Object; XS Unload, Ungarrison or Default) from out at sea.
  Whether they moved at all wasn't seen.

Six Light Transports, loaded by XS with 3 Clubmen each, all sail first (Move) to the water at the beach's edge, then
each tries another way to land. Chat says where each is (its x) and what it carries whenever that changes, and how
many Clubmen stand outside a transport.
- T1-T4 are player 2's (the Legion's stand-in, with the "immobile" AI as in the run: units hold position):
  T1 Unload (task 9), T2 Ungarrison (task 13), T3 XS sets each passenger's `cUnitGarrisonedInId` to -1, T4 the
  fallback: the passengers are removed and the same units created on the beach.
- T5-T6 are player 3's, with no AI at all ("none"): T5 Unload (task 9), T6 the trigger Unload effect.
"""

from aoe2ed import tables
from aoe2ed.tools.world import map_set_terrain, player_set

NAME = "outposts"
BOONS = ()
BUTTONS = {}
PLAYERS = 3
OWNERS = (2, 2, 2, 2, 3, 3)  # T1-T6
NO_AI = 3
TRANSPORT = 545  # Light Transport
CARRIED = 3  # Clubmen in each transport
WATER = 1
SEA_X = 36  # water from here east
BEACH_X = 33  # a land tile
NEAR_X = 37  # water next to the beach
SPAWN_X = 48
CREATE_AT, SEND_AT, LAND_AT = 3, 6, 25  # seconds
ROWS = (0, 2, 4, 6, 8, 10)  # T1-T6, from the strip's top
UNLOAD, UNGARRISON = 9, 13  # tasks (the trigger ActionType numbers; the docs' cctionTypeUnload isn't in the game)


def setup(session, ctx, techs: dict[str, int], top: int) -> str:
    s = session.scenario
    size = s.map_manager.map_size
    clubman = tables.object_id("CLUBMAN", "ror")
    player_set(session.handle, NO_AI, {"ai": "none"})
    map_set_terrain(session.handle, WATER, area=[SEA_X, top - 1, size - 1, top + 11])
    rows = [top + r for r in ROWS]
    t6 = rows[5]
    ctx.trigger(
        "Outposts check: T6 lands by the trigger Unload",
        [{"type": "timer", "timer": LAND_AT}],
        [
            {
                "type": "unload",
                "source_player": NO_AI,
                "object_list_unit_id": TRANSPORT,
                "area": [NEAR_X - 2, t6 - 1, NEAR_X + 3, t6 + 1],
                "location": [BEACH_X, t6],
            },
            {"type": "send_chat", "source_player": 1, "message": "T6 told to unload (trigger)"},
        ],
    )
    sets = [f"    xsArraySetInt(crucibleCheckRow, {n}, {y});" for n, y in enumerate(rows)]
    sets += [f"    xsArraySetInt(crucibleCheckOwner, {n}, {p});" for n, p in enumerate(OWNERS)]
    count = len(ROWS)

    ctx.xs(
        f"""// ---- outposts check: landing from a transport ----
int crucibleCheckT = -1;  // the transports
int crucibleCheckRow = -1;  // their rows (y)
int crucibleCheckOwner = -1;
int crucibleCheckCarried = -1;  // what each carried, last said
int crucibleCheckX = -1;  // where each was (x), last said
int crucibleCheckAshore = -1;
int crucibleCheckOne = -1;
int crucibleCheckIds = -1;

vector crucibleCheckAt(float x = 0.0, int n = 0) {{
    float y = xsArrayGetInt(crucibleCheckRow, n);

    return (xsVectorSet(x + 0.5, y + 0.5, 0.0));
}}

void crucibleCheckTask(int n = 0, int action = -1, float x = 0.0) {{
    xsArraySetInt(crucibleCheckOne, 0, xsArrayGetInt(crucibleCheckT, n));
    xsTaskUnits(crucibleCheckOne, action, crucibleCheckAt(x, n));
}}

// T3: each passenger's garrisoned-in set to none; T4: each passenger removed and made again on the beach.
void crucibleCheckEject(int n = 0, bool remake = false) {{
    int inside = xsGetGarrisonedUnitIds(xsArrayGetInt(crucibleCheckT, n));
    int u = -1;
    float x = {BEACH_X}.0;

    for (i = 0; < xsArrayGetSize(inside)) {{
        u = xsArrayGetInt(inside, i);

        if (remake) {{
            xsCreateUnit(xsGetUnitType(u), xsArrayGetInt(crucibleCheckOwner, n), crucibleCheckAt(x, n), false, false,
                false);
            xsSetUnitProperty(u, cUnitHitpoints, 0);
        }} else {{
            xsSetUnitProperty(u, cUnitGarrisonedInId, -1);
        }}
    }}
}}

int crucibleCheckOutside() {{
    int found = 0;

    for (p = 2; <= 3) {{
        crucibleCheckIds = xsGetPlayerUnitIds(p, {clubman}, crucibleCheckIds);

        for (i = 0; < xsArrayGetSize(crucibleCheckIds)) {{
            if (xsGetGarrisonedInUnitId(xsArrayGetInt(crucibleCheckIds, i)) < 0) {{
                found++;
            }}
        }}
    }}

    return (found);
}}

rule crucibleCheckTransports
    active
    minInterval 1
{{
    int t = xsGetTime();
    int c = -1;
    int value = 0;
    float x = 0.0;

    if (t >= {CREATE_AT} && crucibleCheckT < 0) {{
        crucibleCheckT = xsArrayCreateInt({count}, -1, "crucibleCheckT");
        crucibleCheckRow = xsArrayCreateInt({count}, 0, "crucibleCheckRow");
        crucibleCheckOwner = xsArrayCreateInt({count}, 0, "crucibleCheckOwner");
        crucibleCheckCarried = xsArrayCreateInt({count}, -1, "crucibleCheckCarried");
        crucibleCheckX = xsArrayCreateInt({count}, -1, "crucibleCheckX");
        crucibleCheckOne = xsArrayCreateInt(1, -1, "crucibleCheckOne");
        crucibleCheckIds = xsArrayCreateInt(1, -1, "crucibleCheckIds");
{chr(10).join(sets)}
        for (n = 0; < {count}) {{
            x = {SPAWN_X}.0;
            xsArraySetInt(crucibleCheckT, n, xsCreateUnit({TRANSPORT}, xsArrayGetInt(crucibleCheckOwner, n),
                crucibleCheckAt(x, n), false, false, false));

            for (k = 0; < {CARRIED}) {{
                x = {BEACH_X - 3} - k;
                c = xsCreateUnit({clubman}, xsArrayGetInt(crucibleCheckOwner, n), crucibleCheckAt(x, n), false, false,
                    false);
                xsSetUnitProperty(c, cUnitGarrisonedInId, xsArrayGetInt(crucibleCheckT, n));
            }}
        }}

        xsChatData("Transports created and loaded: %d", {count});
    }}

    if (crucibleCheckT < 0) {{
        return;
    }}

    if (t == {SEND_AT}) {{
        for (n = 0; < {count}) {{
            crucibleCheckTask(n, cActionTypeMove, {NEAR_X}.0);
        }}

        xsChatData("All sent to the beach's edge, x %d", {NEAR_X});
    }}

    if (t == {LAND_AT}) {{
        crucibleCheckTask(0, {UNLOAD}, {BEACH_X}.0);
        crucibleCheckTask(1, {UNGARRISON}, {BEACH_X}.0);
        crucibleCheckEject(2, false);
        crucibleCheckEject(3, true);
        crucibleCheckTask(4, {UNLOAD}, {BEACH_X}.0);
        xsChatData("Landing: T1 unload, T2 ungarrison, T3 eject, T4 remake, T5 unload (no AI): %d", 5);
    }}

    for (n = 0; < {count}) {{
        c = xsArrayGetInt(crucibleCheckT, n);
        value = xsArrayGetSize(xsGetGarrisonedUnitIds(c));

        if (value != xsArrayGetInt(crucibleCheckCarried, n)) {{
            xsArraySetInt(crucibleCheckCarried, n, value);
            xsChatData("T" + (n + 1) + " carries %d", value);
        }}

        value = xsVectorGetX(xsGetUnitPosition(c));

        if (value != xsArrayGetInt(crucibleCheckX, n)) {{
            xsArraySetInt(crucibleCheckX, n, value);

            if (value <= {NEAR_X + 1}) {{
                xsChatData("T" + (n + 1) + " at the beach's edge, x %d", value);
            }}
        }}
    }}

    value = crucibleCheckOutside();

    if (value != crucibleCheckAshore) {{
        crucibleCheckAshore = value;
        xsChatData("Clubmen outside a transport: %d", value);
    }}
}}
"""
    )

    return (
        "Outposts: landing from a transport. Six Light Transports appear at sea to the east, T1 northmost to T6 "
        f"southmost (T1-T4 red with the immobile AI, T5-T6 another colour with no AI), each loaded with {CARRIED} "
        f"Clubmen at {CREATE_AT} s. At {SEND_AT} s all sail to the beach's edge; at {LAND_AT} s each tries to land "
        "another way. Chat says when each reaches the edge, what each carries, and how many Clubmen stand outside "
        "a transport. Note which landed their Clubmen, and whether any transport never reached the edge."
    )
