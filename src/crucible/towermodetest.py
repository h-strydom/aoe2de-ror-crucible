"""The over-the-top tower, round 2 (`crucible_tower_modes`, with the Crucible Test Data mod).

Can native ranges plus automatic switching give a tower arrows at 2-6 and a boulder within 2? Round 1 (arrows as the
normal attack, the boulder as a charge-type-6 projectile) fired both at the far enemies only. Round 2 flips it: the
boulder is the normal attack (range 2) and the arrows a charge projectile with its own range 2-6, with three AoE2
units' charge settings (Fire Lancer, Hearth Troop, Fire Archer); a fourth tower keeps round 1's order with the
boulder's own range set to 0-2. See testmod.TOWER_STYLES. The Fire Lancer tower has two repeatable techs, "Ballista
mode" and "Arrow mode", which upgrade it into a ballista tower and back. Passive enemy Clubmen stand 1.5 tiles
(boulder range) and 5 tiles (arrow range) from each tower.

A script logs the tracked Clubmen's HP every 2 s to `<profile>/profile/crucible_tower_modes.xsdat`;
`crucible tower-modes-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import TOWER_STYLES, tower_mode_ids

NAME = "crucible_tower_modes"
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322004, 2, 1, 2
REVEAL_MAP, MIN_RANGE = 203, 20
ROWS = (8, 22, 36, 50)
SIZE = 64

INSTRUCTIONS = """Crucible tower modes test, round 2. Pick "Crucible Test Data" as the Data Mod. Nothing ends the \
game; watch 2 minutes, then try the buttons.

Four towers, top to bottom, each with passive enemy Clubmen 1.5 tiles away (boulder range) and 5 tiles away (arrow \
range). The top three throw a BOULDER as their normal attack and carry ARROWS as an always-ready charge with their \
own range 2-6, using the charge settings of the Fire Lancer, the Hearth Troop and the Fire Archer. The bottom one is \
the other way round: arrows normally, the boulder as the charge. Which tower hits BOTH the close Clubmen (boulder) and \
the far ones (arrows)?
BALLISTA MODE: the top tower has a "Ballista mode" button (a tech). Research it: does the tower become a ballista \
tower firing bolts, with an "Arrow mode" button to go back? Can you go back and forth more than once?"""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def xs_code(tracked: list[int]) -> str:
    header = "".join(f"    xsWriteInt({v});\n" for v in [MAGIC, VERSION, len(tracked), *tracked])
    hp = "".join(f"    crucibleTowerHp({u});\n" for u in tracked)
    return f"""// ---- crucible tower modes test ----
void crucibleTowerHp(int id = -1) {{
    int v = -1;
    if (xsDoesUnitExist(id)) {{
        v = xsGetUnitHitpoints(id);
    }}
    xsWriteInt(v);
}}

rule crucibleTowerInit
    active
    highFrequency
{{
    xsCreateFile(false);
{header}    xsCloseFile();
    xsDisableSelf();
}}

rule crucibleTowerSample
    active
    minInterval {INTERVAL}
{{
    xsCreateFile(true);
    xsWriteInt({TAG_SAMPLE});
    xsWriteInt(xsGetGameTime());
{hp}    xsCloseFile();
}}
"""


def build(out: Path) -> tuple[Path, list[tuple[str, int]]]:
    ids = tower_mode_ids()
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    tracked: list[tuple[str, int]] = []
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": True,
                                     "population_cap": 200})
            player_set(o.handle, 2, {"civilization": "PERSIAN", "starting_age": "IMPERIAL", "ai": "none"})
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            passive, settings = [], []
            for (label, *_), y in zip(TOWER_STYLES, ROWS):
                _add(s, 1, ids[label], 12, y)
                near = [_add(s, 2, "CLUBMAN", 12 + dx, y + dy) for dx, dy in ((1.5, 0), (1.5, 1), (0, 1.5))]
                far = [_add(s, 2, "CLUBMAN", 17 + dx, y + dy) for dx, dy in ((0, 0), (0, 1.2), (1.2, 0))]
                passive += near + far
                tracked += [(f"{label}: close 1", near[0]), (f"{label}: close 2", near[1]),
                            (f"{label}: far 1", far[0]), (f"{label}: far 2", far[1])]
            _add(s, 1, "TOWN_CENTER", 50, 50)
            blocks.anchor(ctx, player=2, at=(62, 2))
            ctx.trigger("Setup", [], [
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": passive,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}, *settings])
            ctx.xs(xs_code([u for _, u in tracked]))
            ctx.flush_xs()
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 16, "initial_player_view_y": 22})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path, tracked
    finally:
        SESSIONS.close(o.handle)


def labels() -> list[str]:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        return [label for label, _ in build(Path(tmp))[1]]


def report(record: Path, names: list[str]) -> str:
    vals = list(struct.unpack_from(f"<{record.stat().st_size // 4}i", record.read_bytes()))
    if vals[0] != MAGIC:
        raise ValueError("not a crucible tower modes record")
    n = vals[2]
    i, width = 3 + n, 2 + n
    samples = []
    while i + width <= len(vals) and vals[i] == TAG_SAMPLE:
        samples.append(vals[i + 1:i + width])
        i += width
    if not samples:
        return "no samples recorded"
    picks = [r for r in samples if r[0] in (2, 4, 6, 10, 16, 20, 30, 45, 60, 90, 120)] or samples
    rows = ["".ljust(36) + "".join(f"{r[0] // 60}:{r[0] % 60:02}".rjust(7) for r in picks)]
    for k, label in enumerate(names[:n]):
        rows.append(label[:35].ljust(36) + "".join(str(r[1 + k]).rjust(7) for r in picks))
    return "\n".join(rows)
