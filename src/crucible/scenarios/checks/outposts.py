"""Test: what the outposts (docs/outposts.md) need from the engine, before they're built on it.

1. Damage: XS reads a Legion building's HP (`xsGetUnitProperty(id, cUnitHitpoints)`), the outposts' turtle test. A
   Legion Barracks with the player's Clubmen beside it; chat says its HP whenever it changes.
2. Transports: a Light Transport created by trigger, then units created inside it ("Create Garrisoned Object", by
   type in an area, as the run will do for one it just spawned), then landed on the beach: transport A by the Unload
   effect, transport B by a Task Object to a land tile. Chat says each step.
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
BEACH_X = 33
SPAWN_X = 46
CREATE_AT, FILL_AT, LAND_AT = 5, 7, 12  # seconds


def _place(s, unit: int, x: int, y: int, player: int = 1) -> None:
    s.unit_manager.add_unit(player=player, unit_const=unit, x=x + 0.5, y=y + 0.5)


def _at(seconds: int) -> list[dict]:
    return [{"type": "timer", "timer": seconds}]


def _say(text: str) -> dict:
    return {"type": "send_chat", "source_player": 1, "message": text}


def _transport(ctx, name: str, y: int, clubman: int, land: dict) -> None:
    area = [SPAWN_X - 2, y - 2, SPAWN_X + 2, y + 2]
    ctx.trigger(
        f"Outposts check: transport {name} created",
        _at(CREATE_AT),
        [
            {
                "type": "create_object",
                "source_player": LEGION,
                "object_list_unit_id": TRANSPORT,
                "location": [SPAWN_X, y],
            },
            _say(f"Transport {name}: created"),
        ],
    )
    fill = {
        "type": "create_garrisoned_object",
        "source_player": LEGION,
        "object_list_unit_id": TRANSPORT,
        "object_list_unit_id_2": clubman,
        "area": area,
    }
    ctx.trigger(
        f"Outposts check: transport {name} filled",
        _at(FILL_AT),
        [*[fill] * CARRIED, _say(f"Transport {name}: {CARRIED} Clubmen created inside")],
    )
    ctx.trigger(
        f"Outposts check: transport {name} lands",
        _at(LAND_AT),
        [
            {**land, "source_player": LEGION, "object_list_unit_id": TRANSPORT, "area": area},
            _say(f"Transport {name}: sent to land"),
        ],
    )


def setup(session, ctx, techs: dict[str, int], top: int) -> str:
    s = session.scenario
    size = s.map_manager.map_size
    clubman = tables.object_id("CLUBMAN", "ror")
    barracks = tables.object_id("BARRACKS", "ror")
    map_set_terrain(session.handle, WATER, area=[SEA_X, top - 1, size - 1, top + 11])

    _place(s, barracks, 18, top + 3, player=LEGION)

    for n in range(6):
        _place(s, clubman, 16 + n, top + 8)

    a, b = top + 2, top + 8
    _transport(ctx, "A", a, clubman, {"type": "unload", "location": [BEACH_X, a]})
    _transport(ctx, "B", b, clubman, {"type": "task_object", "location": [BEACH_X, b]})

    ctx.xs(
        f"""// ---- outposts check: a Legion building's HP ----
int crucibleCheckHp = -2;

rule crucibleCheckOutpostHp
    active
    minInterval 1
{{
    int ids = xsGetPlayerUnitIds({LEGION}, {barracks}, -1);
    int hp = -1;

    if (xsArrayGetSize(ids) > 0) {{
        hp = xsGetUnitProperty(xsArrayGetInt(ids, 0), cUnitHitpoints);
    }}

    if (hp != crucibleCheckHp) {{
        crucibleCheckHp = hp;
        xsChatData("Legion Barracks HP: %d", hp);
    }}
}}
"""
    )

    return f"""Outposts. 1) Attack the red Barracks with your 6 Clubmen: chat should say "Legion Barracks HP: n" \
each time it changes (-1 once it's gone). 2) Two red Light Transports appear at sea to the east at {CREATE_AT} s, get \
{CARRIED} Clubmen each at {FILL_AT} s, and are sent to the beach at {LAND_AT} s: A (north) by Unload, B (south) by \
Task Object. Say which transport carried its Clubmen and put them ashore."""
