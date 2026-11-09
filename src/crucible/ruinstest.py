"""The ruins and artifacts test: ruins that trickle resources, artifact carts that speed up every Barracks.

A standalone scenario, `crucible_ruins_test`. No data mod needed.

Ruins trickle, one allied player each (they own their objects from the start):

| Player | Test |
|---|---|
| 2 | Owns Artifact Ruins, with King of the Hill's monument trickles (221-224) at 1, as the KotH tech sets them |
| 3 | Owns the KotH Monument, same trickles: the reference |
| 4 | Owns Artifact Ruins; a script pays 5 food, wood, stone and gold a minute per ruin owned |
| 5 | Owns Artifact Ruins, nothing else: the control |

Ruins and the Monument both carry resource storage 14 (counted while owned), so KotH's trickle may pay for ruins too.

You (player 1) have the same monument trickles, a Gaia ruin to capture, two artifact carts and two Barracks. The left
Barracks is unchanged; the right one's garrison type is opened up (127) on that Barracks. While any artifact is
garrisoned in any of your Barracks, a script sets every Barracks' work rate to 30, so units train in about a second;
it goes back to 1 when the artifacts leave.

A script logs every player's stockpile, and your Barracks' state, every 10 seconds to
`<profile>/profile/crucible_ruins_test.xsdat`; `crucible ruins-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_ruins_test"
SIZE = 64
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412321222, 1, 1, 10
PLAYERS = range(1, 6)
MONUMENT_TRICKLES = (221, 222, 223, 224)        # Monument Food/Wood/Stone/Gold Trickle
RUINS, MONUMENT, ARTIFACT_CART = 52, 826, 159
ARTIFACTS = (25, 44, 159, 944, 1304)
BARRACKS = (12, 20, 132, 498)                   # the Barracks and its age looks
GARRISON_TYPE, WORK_RATE, SET = 30, 13, 1
FAST_WORK_RATE = 30                             # Clubman 26 s / 30 is under a second
SCRIPT_PAY, SCRIPT_PLAYER = 5, 4                # per ruin per minute
REVEAL_MAP = 203
LANE_Y = {p: 6 + (p - 2) * 8 for p in (2, 3, 4, 5)}

INSTRUCTIONS = """Crucible ruins and artifacts test. The map is revealed; nothing ends the game. Run it 3-4 minutes.

RUINS: allied players along the left own a ruin or the Monument from the start. P2 ruin with King of the Hill's \
monument trickle | P3 the KotH Monument, same trickle | P4 ruin, a script pays 5 of everything a minute | P5 ruin, \
nothing (control). Their resources are logged. You have the same monument trickle: capture the Gaia ruin near \
your units (walk a unit to it) and watch your resources.

ARTIFACTS: send an artifact cart into a Barracks (the right one admits more than the left). While any artifact is \
inside any of your Barracks, every Barracks should train in about a second. Can carts enter? Does training speed up \
in BOTH Barracks? Take the cart out: does it slow down again?"""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code() -> str:
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(PLAYERS)])
    stock = "".join(f"        xsWriteInt(xsPlayerAttribute(p, {a}));\n" for a in (0, 1, 2, 3, 14))
    is_artifact = " || ".join(f"o == {a}" for a in ARTIFACTS)
    barracks_loop = "".join(f"""    list = xsGetPlayerUnitIds(1, {b});
    for (i = 0; < xsArrayGetSize(list)) {{
        inside = xsGetGarrisonedUnitIds(xsArrayGetInt(list, i));
        for (k = 0; < xsArrayGetSize(inside)) {{
            o = xsGetUnitObjectId(xsArrayGetInt(inside, k));
            if ({is_artifact}) {{
                found = found + 1;
            }}
        }}
    }}
""" for b in BARRACKS)
    set_rate = "".join(f"        xsEffectAmount(0, {b}, {WORK_RATE}, rate, 1);\n" for b in BARRACKS)
    return f"""// ---- crucible ruins and artifacts test ----
int crucibleArtifactsIn = 0;
int crucibleRuinsPaid = 0;

rule crucibleRuinsInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleRuinsSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
    for (p = 1; < {len(PLAYERS) + 1}) {{
{stock}    }}
    xsWriteInt(crucibleArtifactsIn);
    xsCloseFile();
}}

rule crucibleRuinsScriptPay
    active
    minInterval 60
{{
    int ruins = xsGetObjectCount({SCRIPT_PLAYER}, {RUINS});
    for (r = 0; < 4) {{
        xsSetPlayerAttribute({SCRIPT_PLAYER}, r, xsPlayerAttribute({SCRIPT_PLAYER}, r) + {SCRIPT_PAY} * ruins);
    }}
}}

rule crucibleArtifactBarracks
    active
    minInterval 1
{{
    int found = 0;
    int list = -1;
    int inside = -1;
    int o = -1;
{barracks_loop}    if ((found > 0) != (crucibleArtifactsIn > 0)) {{
        float rate = 1.0;
        if (found > 0) {{
            rate = {FAST_WORK_RATE}.0;
            xsChatData("Artifact in a Barracks: every Barracks trains fast (%d)", found);
        }} else {{
            xsChatData("No artifact in a Barracks: normal training", 0);
        }}
{set_rate}    }}
    crucibleArtifactsIn = found;
}}
"""


def build(out: Path) -> Path:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = len(PLAYERS)
            for p in PLAYERS:
                fields = {"civilization": "GREEK", "starting_age": "CASTLE", "human": p == 1,
                          "food": 1000 if p == 1 else 0, "wood": 1000 if p == 1 else 0,
                          "gold": 1000 if p == 1 else 0, "stone": 0, "population_cap": 200}
                if p > 1:
                    fields["ai"] = "none"
                player_set(o.handle, p, fields)
            for p in PLAYERS:
                diplomacy_set(o.handle, p, [q for q in PLAYERS if q != p], "ALLY", mutual=False)
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            settings = []
            for p, obj in ((2, RUINS), (3, MONUMENT), (4, RUINS), (5, RUINS)):
                _add(s, p, obj, 8, LANE_Y[p])
                blocks.anchor(ctx, player=p, at=(1, LANE_Y[p]))
            for p in (1, 2, 3):
                settings += [{"type": "modify_resource", "source_player": p, "tribute_list": a, "operation": "SET",
                              "quantity": 1} for a in MONUMENT_TRICKLES]

            # Player 1: a Gaia ruin to capture, two artifact carts, two Barracks.
            _add(s, 0, RUINS, 30, 12)
            for k in range(3):
                _add(s, 1, "HOPLITE", 26 + k, 16)
            for k in range(2):
                _add(s, 1, ARTIFACT_CART, 34 + k * 2, 30)
            _add(s, 1, "BARRACKS", 30, 36)                    # left: unchanged
            right = _add(s, 1, "BARRACKS", 42, 36)
            settings.append({"type": "modify_object_attribute", "source_player": 1, "selected_object_ids": [right],
                             "object_attributes": GARRISON_TYPE, "operation": SET, "quantity": 127})
            _add(s, 1, "TOWN_CENTER", 50, 54)
            for i in range(4):
                _add(s, 1, "VILLAGER_MALE", 46 + i, 50)
            settings.append({"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1,
                             "quantity": 2, "operation": "SET"})
            ctx.trigger("Setup", [], settings)
            ctx.xs(xs_code())
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 34, "initial_player_view_y": 26})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)


def report(record: Path) -> str:
    vals = list(struct.unpack_from(f"<{record.stat().st_size // 4}i", record.read_bytes()))
    if vals[0] != MAGIC:
        raise ValueError("not a crucible ruins test record")
    n = vals[2]
    i, width = 3, n * 5 + 1
    lines = ["food/wood/stone/gold and resource 14 per player; artifacts in your Barracks"]
    while i + 2 + width <= len(vals) and vals[i] == TAG_SAMPLE:
        t, row = vals[i + 1], vals[i + 2:i + 2 + width]
        players = "  ".join(f"P{p + 1} {'/'.join(map(str, row[p * 5:p * 5 + 4]))} r14={row[p * 5 + 4]}"
                            for p in range(n))
        lines.append(f"{t // 60}:{t % 60:02}  {players}  artifacts in barracks {row[-1]}")
        i += 2 + width
    return "\n".join(lines)
