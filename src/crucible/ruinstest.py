"""The ruins and artifacts test, round 3: ruins that trickle resources, artifacts that garrison and speed up every Barracks.

A standalone scenario, `crucible_ruins_test`, played with the Crucible Test Data mod picked (it adds the Ruin
Monument, a copy of King of the Hill's Monument dressed as Artifact Ruins).

Round 1 (2026-11-09): KotH's monument trickle pays for the Monument but not for Artifact Ruins; Relic Carts can't
garrison (artifacts match no garrison category), and the carts used were AoE2-looking relic carts, not the AoE1
artifact (unit 25).

Ruins trickle, one allied player each (they own their objects from the start):

| Player | Test |
|---|---|
| 2 | Owns a **Ruin Monument** (data mod), with KotH's monument trickles at 1 |
| 3 | Owns the KotH Monument, same trickles: the reference |
| 4 | Owns Artifact Ruins; a **script** pays 1 food, wood, stone and gold every 10 s per ruin owned |
| 5 | Owns Artifact Ruins, nothing else: the control |

You (player 1) have the monument trickles, a Gaia Ruin Monument and a Gaia Artifact Ruins to capture, two Barracks
and three artifacts, all given a garrison task by the data mod: the AoE1 artifact (25, artifact class), a copy in the
infantry class and a copy in the priest class (round 3: which class lets an artifact garrison?). The data mod opens
every Barracks to every garrison category. While any artifact is garrisoned in, or stands within 4 tiles of, one of
your Barracks, a script sets every Barracks' work rate to 30 (units train in about a second); it goes back to 1 when
none is.

Round 2 (2026-11-09): the Ruin Monument and script pay both trickle; the AoE1 artifact has no garrison button.

A script logs every player's stockpile and objects every 10 seconds to `<profile>/profile/crucible_ruins_test.xsdat`;
`crucible ruins-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import artifact_ids, ruin_monument_id

NAME = "crucible_ruins_test"
SIZE = 64
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412321222, 3, 1, 10
PLAYERS = range(1, 6)
MONUMENT_TRICKLES = (221, 222, 223, 224)        # Monument Food/Wood/Stone/Gold Trickle
RUINS, MONUMENT, ARTIFACT = 52, 826, 25        # Artifact Ruins, KotH Monument, the AoE1 Artifact
BARRACKS = (12, 20, 132, 498)                   # the Barracks and its age looks
WORK_RATE, FAST_WORK_RATE, DELIVER_DISTANCE = 13, 30, 4.0
SCRIPT_PAY, SCRIPT_PLAYER = 1, 4                # per ruin every 10 s
REVEAL_MAP = 203
LANE_Y = {p: 6 + (p - 2) * 8 for p in (2, 3, 4, 5)}

INSTRUCTIONS = """Crucible ruins and artifacts test, round 3. Pick "Crucible Test Data" as the Data Mod. The map is \
revealed; nothing ends the game. Run it 3 minutes or more.

RUINS: allied players along the left own an object from the start. P2 a Ruin Monument (a KotH Monument that looks \
like ruins) with KotH's trickle | P3 the KotH Monument, same trickle | P4 ruins, a script pays 1 of everything every \
10 s | P5 ruins, nothing (control). You have KotH's trickle too: capture the Gaia Ruin Monument (left of your \
hoplites) and the Gaia ruins (right). Do your resources start rising after the Ruin Monument?

ARTIFACTS: walk an artifact next to a Barracks (within 4 tiles). While any artifact stands near any of your \
Barracks, every Barracks should train in about a second; a chat message announces it. Move it away: does training \
slow down again?"""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(ruin_monument: int, artifacts: tuple[int, ...] = (ARTIFACT,)) -> str:
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(PLAYERS)])
    stock = "".join(f"        xsWriteInt(xsPlayerAttribute(p, {a}));\n" for a in (0, 1, 2, 3)) \
        + f"        xsWriteInt(xsGetObjectCount(p, {RUINS}));\n" \
        + f"        xsWriteInt(xsGetObjectCount(p, {ruin_monument}));\n"
    barracks = "".join(f"""        list = xsGetPlayerUnitIds(1, {b});
        for (k = 0; < xsArrayGetSize(list)) {{
            bp = xsGetUnitPosition(xsArrayGetInt(list, k));
            dx = xsVectorGetX(ap) - xsVectorGetX(bp);
            dy = xsVectorGetY(ap) - xsVectorGetY(bp);
            if (dx * dx + dy * dy <= {DELIVER_DISTANCE * DELIVER_DISTANCE}) {{
                found = found + 1;
            }}
        }}
""" for b in BARRACKS)
    is_artifact = " || ".join(f"(o == {a})" for a in artifacts)
    garrisoned = "".join(f"""    list = xsGetPlayerUnitIds(1, {b});
    for (k = 0; < xsArrayGetSize(list)) {{
        inside = xsGetGarrisonedUnitIds(xsArrayGetInt(list, k));
        for (g = 0; < xsArrayGetSize(inside)) {{
            o = xsGetUnitObjectId(xsArrayGetInt(inside, g));
            if ({is_artifact}) {{
                held = held + 1;
            }}
        }}
    }}
""" for b in BARRACKS)
    near = "".join(f"""    artifacts = xsGetPlayerUnitIds(1, {a});
    for (i = 0; < xsArrayGetSize(artifacts)) {{
        ap = xsGetUnitPosition(xsArrayGetInt(artifacts, i));
{barracks}    }}
""" for a in artifacts)
    set_rate = "".join(f"        xsEffectAmount(0, {b}, {WORK_RATE}, rate, 1);\n" for b in BARRACKS)
    return f"""// ---- crucible ruins and artifacts test, round 3 ----
int crucibleArtifactsNear = 0;
int crucibleArtifactsHeld = 0;

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
    xsWriteInt(crucibleArtifactsNear);
    xsWriteInt(crucibleArtifactsHeld);
    xsCloseFile();
}}

rule crucibleRuinsScriptPay
    active
    minInterval 10
{{
    int ruins = xsGetObjectCount({SCRIPT_PLAYER}, {RUINS});
    for (r = 0; < 4) {{
        xsSetPlayerAttribute({SCRIPT_PLAYER}, r, xsPlayerAttribute({SCRIPT_PLAYER}, r) + {SCRIPT_PAY} * ruins);
    }}
}}

rule crucibleArtifactDelivery
    active
    minInterval 1
{{
    int found = 0;
    int list = -1;
    vector bp = cInvalidVector;
    float dx = 0.0;
    float dy = 0.0;
    int held = 0;
    int o = -1;
    int inside = -1;
    int artifacts = -1;
    vector ap = cInvalidVector;
{near}{garrisoned}    if (held != crucibleArtifactsHeld) {{
        xsChatData("Artifacts garrisoned in your Barracks: %d", held);
    }}
    if ((found + held > 0) != (crucibleArtifactsNear + crucibleArtifactsHeld > 0)) {{
        float rate = 1.0;
        if (found + held > 0) {{
            rate = {FAST_WORK_RATE}.0;
            xsChatData("Artifact at or in a Barracks: every Barracks trains fast", 0);
        }} else {{
            xsChatData("No artifact at a Barracks: normal training", 0);
        }}
{set_rate}    }}
    crucibleArtifactsNear = found;
    crucibleArtifactsHeld = held;
}}
"""


def build(out: Path) -> Path:
    ruin_monument = ruin_monument_id()
    infantry_artifact, priest_artifact = artifact_ids()
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
            for p, obj in ((2, ruin_monument), (3, MONUMENT), (4, RUINS), (5, RUINS)):
                _add(s, p, obj, 8, LANE_Y[p])
                blocks.anchor(ctx, player=p, at=(1, LANE_Y[p]))
            for p in (1, 2, 3):
                settings += [{"type": "modify_resource", "source_player": p, "tribute_list": a, "operation": "SET",
                              "quantity": 1} for a in MONUMENT_TRICKLES]

            # Player 1: Gaia objects to capture, two AoE1 artifacts, two Barracks.
            _add(s, 0, ruin_monument, 22, 12)
            _add(s, 0, RUINS, 36, 12)
            for k in range(3):
                _add(s, 1, "HOPLITE", 28 + k, 16)
            for k, unit in enumerate((ARTIFACT, infantry_artifact, priest_artifact)):
                _add(s, 1, unit, 32 + k * 3, 28)
            _add(s, 1, "BARRACKS", 28, 38)
            _add(s, 1, "BARRACKS", 44, 38)
            _add(s, 1, "TOWN_CENTER", 50, 54)
            for i in range(4):
                _add(s, 1, "VILLAGER_MALE", 46 + i, 50)
            settings.append({"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1,
                             "quantity": 2, "operation": "SET"})
            ctx.trigger("Setup", [], settings)
            ctx.xs(xs_code(ruin_monument, (ARTIFACT, *artifact_ids())))
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
    version, n = vals[1], vals[2]
    per = 6 if version >= 2 else 5
    extra = 2 if version >= 3 else 1
    i, width = 3, n * per + extra
    lines = ["food/wood/stone/gold per player, ruins and Ruin Monuments owned; artifacts at your Barracks"]
    while i + 2 + width <= len(vals) and vals[i] == TAG_SAMPLE:
        t, row = vals[i + 1], vals[i + 2:i + 2 + width]
        players = "  ".join(f"P{p + 1} {'/'.join(map(str, row[p * per:p * per + 4]))} "
                            f"ruins={row[p * per + 4]} rm={row[p * per + 5] if per == 6 else '-'}"
                            for p in range(n))
        held = f", garrisoned {row[-1]}" if extra == 2 else ""
        lines.append(f"{t // 60}:{t % 60:02}  {players}  artifacts near barracks {row[n * per]}{held}")
        i += 2 + width
    return "\n".join(lines)
