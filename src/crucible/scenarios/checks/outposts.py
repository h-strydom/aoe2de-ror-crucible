"""Test: how the sea outposts (docs/outposts.md) land a wave from a transport.

Confirmed 2026-11-23, so gone from here: XS reads a building's HP (`xsGetUnitProperty(id, cUnitHitpoints)`); and the
trigger route failed: a Light Transport created by trigger, filled by "Create Garrisoned Object" and sent by the Unload
effect or a Task Object to a beach tile, put nobody ashore.

Four Legion Light Transports, created by XS at sea, each tried another way (the XS rule below). Chat says what each
carries whenever it changes, and how many Clubmen are ashore.
- T1: loaded by XS (`cUnitGarrisonedInId` set on Clubmen made on the beach), sailed next to the beach (Move), then
  told to Unload (`cctionTypeUnload`: the game's own spelling) onto the beach.
- T2: loaded by XS, told to Ungarrison onto the beach from out at sea.
- T3: loaded by XS, given a Default order onto a beach tile from out at sea.
- T4: filled by the trigger effect "Create Garrisoned Object" (did that work?), then told to Unload from out at sea.
"""

from aoe2ed import tables
from aoe2ed.tools.world import map_set_terrain

NAME = "outposts"
BOONS = ()
BUTTONS = {}
PLAYERS = 2
LEGION = 2  # the Legion's stand-in here
TRANSPORT = 545  # Light Transport
CARRIED = 3  # Clubmen in each transport
WATER = 1
SEA_X = 36  # water from here east
BEACH_X = 33  # a land tile
NEAR_X = 37  # water next to the beach
SPAWN_X = 48
CREATE_AT, FILL_AT, SEND_AT, UNLOAD_AT = 3, 5, 8, 25  # seconds
ROWS = (1, 4, 7, 10)  # T1-T4, from the strip's top


def setup(session, ctx, techs: dict[str, int], top: int) -> str:
    s = session.scenario
    size = s.map_manager.map_size
    clubman = tables.object_id("CLUBMAN", "ror")
    map_set_terrain(session.handle, WATER, area=[SEA_X, top - 1, size - 1, top + 11])
    rows = [top + r for r in ROWS]
    ctx.trigger(
        "Outposts check: T4 filled by trigger",
        [{"type": "timer", "timer": FILL_AT}],
        [
            {
                "type": "create_garrisoned_object",
                "source_player": LEGION,
                "object_list_unit_id": TRANSPORT,
                "object_list_unit_id_2": clubman,
                "area": [SPAWN_X - 2, rows[3] - 2, SPAWN_X + 2, rows[3] + 2],
            }
        ]
        * CARRIED,
    )
    ys = "\n".join(f"    xsArraySetInt(crucibleCheckRow, {n}, {y});" for n, y in enumerate(rows))

    ctx.xs(
        f"""// ---- outposts check: landing from a transport ----
int crucibleCheckT = -1;  // the 4 transports
int crucibleCheckRow = -1;  // their rows (y)
int crucibleCheckCarried = -1;  // what each carried, last said
int crucibleCheckAshore = -1;
int crucibleCheckOne = -1;

vector crucibleCheckAt(float x = 0.0, int n = 0) {{
    float y = xsArrayGetInt(crucibleCheckRow, n);

    return (xsVectorSet(x + 0.5, y + 0.5, 0.0));
}}

void crucibleCheckTask(int n = 0, int action = -1, float x = 0.0) {{
    xsArraySetInt(crucibleCheckOne, 0, xsArrayGetInt(crucibleCheckT, n));
    xsTaskUnits(crucibleCheckOne, action, crucibleCheckAt(x, n));
}}

rule crucibleCheckTransports
    active
    minInterval 1
{{
    int t = xsGetTime();
    int c = -1;
    float x = 0.0;
    int carried = 0;

    if (t >= {CREATE_AT} && crucibleCheckT < 0) {{
        crucibleCheckT = xsArrayCreateInt(4, -1, "crucibleCheckT");
        crucibleCheckRow = xsArrayCreateInt(4, 0, "crucibleCheckRow");
        crucibleCheckCarried = xsArrayCreateInt(4, -1, "crucibleCheckCarried");
        crucibleCheckOne = xsArrayCreateInt(1, -1, "crucibleCheckOne");
{ys}
        for (n = 0; < 4) {{
            xsArraySetInt(crucibleCheckT, n, xsCreateUnit({TRANSPORT}, {LEGION}, crucibleCheckAt({SPAWN_X}.0, n), false,
                false, false));
        }}

        for (n = 0; < 3) {{
            for (k = 0; < {CARRIED}) {{
                x = {BEACH_X - 3} - k;
                c = xsCreateUnit({clubman}, {LEGION}, crucibleCheckAt(x, n), false, false, false);
                xsSetUnitProperty(c, cUnitGarrisonedInId, xsArrayGetInt(crucibleCheckT, n));
            }}
        }}

        xsChatData("Transports created, T1-T3 loaded by XS: %d", 3);
    }}

    if (crucibleCheckT < 0) {{
        return;
    }}

    if (t == {SEND_AT}) {{
        crucibleCheckTask(0, cActionTypeMove, {NEAR_X}.0);
        crucibleCheckTask(1, cActionTypeUngarrison, {BEACH_X}.0);
        crucibleCheckTask(2, cActionTypeDefault, {BEACH_X}.0);
        crucibleCheckTask(3, cctionTypeUnload, {BEACH_X}.0);
        xsChatData("Sent: T1 to the beach's edge, T2 ungarrison, T3 default, T4 unload: %d", 4);
    }}

    if (t == {UNLOAD_AT}) {{
        crucibleCheckTask(0, cctionTypeUnload, {BEACH_X}.0);
        xsChatData("T1 told to unload: %d", 1);
    }}

    for (n = 0; < 4) {{
        carried = xsArrayGetSize(xsGetGarrisonedUnitIds(xsArrayGetInt(crucibleCheckT, n)));

        if (carried != xsArrayGetInt(crucibleCheckCarried, n)) {{
            xsArraySetInt(crucibleCheckCarried, n, carried);
            xsChatData("T" + (n + 1) + " carries %d", carried);
        }}
    }}

    carried = xsGetObjectCount({LEGION}, {clubman});

    if (carried != crucibleCheckAshore) {{
        crucibleCheckAshore = carried;
        xsChatData("Red Clubmen not in a transport: %d", carried);
    }}
}}
"""
    )

    return (
        "Outposts: landing from a transport. Four red Light Transports appear at sea to the east at "
        f"{CREATE_AT} s (T1 the northmost, T4 the southmost); T1-T3 get {CARRIED} Clubmen each from XS, T4 from a "
        f"trigger at {FILL_AT} s. At {SEND_AT} s: T1 sails to the beach's edge (and is told to unload at {UNLOAD_AT} "
        "s), T2 is told to ungarrison onto the beach, T3 is given a plain order onto the beach, T4 is told to unload. "
        "Chat says what each carries as it changes. Note which transports put their Clubmen ashore, and the chat "
        "lines."
    )
