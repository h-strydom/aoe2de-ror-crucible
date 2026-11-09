"""The over-the-top tower (`crucible_tower_modes`, with the Crucible Test Data mod).

Two data-mod towers fire arrows with a 2-tile minimum range and carry a charge-type-6 boulder (30 melee, splash) for
enemies inside that range, each with different charge settings (testmod.TOWER_CHARGES); each can switch to a
ballista twin (trait 8). A plain Sentry Tower given the same minimum range by trigger is the control. Passive enemy
Clubmen stand next to each tower (inside the minimum range) and further out.

A script logs the tracked Clubmen's HP every 2 s to `<profile>/profile/crucible_tower_modes.xsdat`;
`crucible tower-modes-report` prints it.
"""
from __future__ import annotations

import struct
from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from .testmod import SENTRY_TOWER, TOWER_CHARGES, TOWER_MIN_RANGE, tower_mode_ids

NAME = "crucible_tower_modes"
SIZE = 48
MAGIC, VERSION, TAG_SAMPLE, INTERVAL = 412322004, 1, 1, 2
REVEAL_MAP, MIN_RANGE = 203, 20
ROWS = (8, 22, 36)

INSTRUCTIONS = """Crucible tower modes test. Pick "Crucible Test Data" as the Data Mod. Nothing ends the game; watch \
2 minutes, then try the switch.

Three towers, each with passive enemy Clubmen right beside it (inside a 2-tile minimum range) and more further out:
TOP: data tower with the Hearth Troop's charge settings. MIDDLE: data tower with the Fire Archer's. BOTTOM: a plain \
Sentry Tower with minimum range 2 (control: it should never hit the close ones).
Do the top two shoot arrows at the far Clubmen and lob a boulder (splash) at the close ones?
Then select a data tower: is there a button to switch it to ballista mode? Does it then fire bolts?"""


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
            towers = [(ids[label], label) for label, _, _ in TOWER_CHARGES] + [(SENTRY_TOWER, "control Sentry")]
            for (unit, label), y in zip(towers, ROWS):
                tower = _add(s, 1, unit, 12, y)
                if unit == SENTRY_TOWER:
                    settings.append({"type": "modify_object_attribute", "source_player": 1,
                                     "selected_object_ids": [tower], "object_attributes": MIN_RANGE,
                                     "operation": 1, "quantity": int(TOWER_MIN_RANGE)})
                near = [_add(s, 2, "CLUBMAN", 12 + dx, y + dy) for dx, dy in ((1.5, 0), (1.5, 1), (0, 1.5))]
                far = [_add(s, 2, "CLUBMAN", 18 + dx, y + dy) for dx, dy in ((0, 0), (0, 1.2), (1.2, 0))]
                passive += near + far
                tracked += [(f"{label}: close 1", near[0]), (f"{label}: close 2", near[1]),
                            (f"{label}: far 1", far[0]), (f"{label}: far 2", far[1])]
            _add(s, 1, "TOWN_CENTER", 40, 40)
            blocks.anchor(ctx, player=2, at=(46, 2))
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
