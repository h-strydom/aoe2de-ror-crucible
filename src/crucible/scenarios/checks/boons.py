"""Test: every tier of every boon (crucible.boons) does what it should, shown on the units it changes and read back
from the game. Kept, unlike other checks: it's rebuilt from crucible.boons, so it can't go stale; rerun it after
changing boons (confirmed all as expected, 2026-11-21).

On the map: for each tier, the units its commands change (with the earlier units of a line: the Clubman for an
Axeman boon), owned by the player that gets that tier, each labelled with what it should now be: the caption over
it (if units show one) and its name, e.g. "Sumerians 1 Common: HP 25 -> 30". Click a unit to compare. The tiers are
spread over players 2 to 8 so no two on a player change a value another's label shows, or the same tech's cost
(assign()): every label's
"before" is the unit's own base value (the Greek civ's, bonus-less, Stone Age).

In the log: XS researches the tier techs one at a time and reads every value their commands change, just before and
just after (the after read waits a tick), into crucible_check.xsdat. report() compares each after with what the
command should make of the before, and each label's before with what the game read: this covers what clicking can't
show (costs, work rate, research times, resources).

Reads (plan()): a unit attribute on the unit, or on one unit of the class (xsGetObjectAttribute; armour and attack
by class); a player resource (xsPlayerAttribute); a tech's cost or research time (xsGetTechAttribute; time at its
first research location). Costs are read per cost slot (Amount First, Second, Third Cost).
"""

import struct
from dataclasses import dataclass
from pathlib import Path

from aoe2ed import tables
from aoe2ed.config import paths
from genieutils.datfile import DatFile

from crucible.bonuses.compile.stats import (
    ADD_ATTRIBUTE,
    ARMOUR,
    ATTACK,
    COST,
    MUL_ATTRIBUTE,
    MUL_RESOURCE,
    RESOURCE,
    SET,
    SET_ATTRIBUTE,
    TECH_COST,
    TECH_TIME,
)
from crucible.boons import catalogue
from crucible.boons.compile import commands
from crucible.boons.model import Boon, Tier
from crucible.datamod import boons as boon_techs
from crucible.datamod.civs import PLAYER as PLAYER_CIV

NAME = "boons"
BOONS: tuple[str, ...] = ()  # the old modifiers: none
BUTTONS: dict[str, int] = {}
PLAYERS = 8
TIER_PLAYERS = range(2, PLAYERS + 1)  # player 1 watches
FILE = "crucible_check.xsdat"
BEFORE, AFTER, DONE = 1, 2, 9
COST_SLOTS = (174, 175, 176)  # Amount First, Second, Third Cost
TECH_COST_ATTRIBUTE, TECH_TIME_ATTRIBUTE = 1, 2  # cTechCost, cTechResearchTime (the XS prelude's values)
SHOWN = 4  # units per tier at most
CELL, ROW, COLUMN = 5, 6, 26  # tiles between units, rows, columns
TOP = 16  # below the check's Wonder
SIZE = 220
NAMES = {
    0: "HP",
    1: "line of sight",
    5: "speed",
    10: "reload",
    12: "range",
    13: "work rate",
    14: "carry",
    21: "population room",
    101: "train time",
    103: "food cost",
    104: "wood cost",
    174: "cost",
    175: "second cost",
    176: "third cost",
}
DAMAGE = {3: "pierce", 4: "melee"}
EXAMPLES = ("watch_tower", "scout_ship", "stone_thrower", "clubman", "priest", "bowman", "scout", "villager")


@dataclass(frozen=True)
class Read:
    """One value to read: kind "object" (unit, attribute, class), "resource" (resource) or "tech" (tech,
    attribute, cost type or location); and what the command should make of it."""

    kind: str
    args: tuple[int, ...]
    op: str  # "set", "add" or "mul"
    amount: float
    command: tuple

    def xs(self, player: int) -> str:
        if self.kind == "object":
            return f"xsGetObjectAttribute({player}, {self.args[0]}, {self.args[1]}, {self.args[2]})"

        if self.kind == "resource":
            return f"xsPlayerAttribute({player}, {self.args[0]})"

        return f"xsGetTechAttribute({player}, {self.args[0]}, {self.args[1]}, {self.args[2]})"

    def expected(self, before: float) -> float:
        if self.op == "set":
            return self.amount

        if self.op == "add":
            return before + self.amount

        return before * self.amount

    @property
    def label(self) -> str:
        """The attribute's name: "HP", "pierce armour"."""
        attribute, damage = self.args[1], self.args[2]

        if attribute in (ARMOUR, ATTACK):
            return f"{DAMAGE.get(damage, f'class {damage}')} {'armour' if attribute == ARMOUR else 'attack'}"

        return NAMES.get(attribute, f"attribute {attribute}")


def _example(data: DatFile, unit_class: int, attribute: int, damage: int) -> int | None:
    """A unit of the class to read, one the player can train if there is one ("enabled" is 0 for all: techs enable
    them); with that attack or armour class if it's one of those."""
    units = data.civs[1].units

    def fits(u) -> bool:
        if not u or u.class_ != unit_class:
            return False

        if attribute in (ARMOUR, ATTACK):
            found = (u.type_50.armours if attribute == ARMOUR else u.type_50.attacks) if u.type_50 else ()
            return any(a.class_ == damage for a in found)

        return True

    def trained(u) -> bool:  # and not a hero (Zenobia's Tower, the Flying Dutchman)
        return bool(
            u.creatable and not u.creatable.hero_mode and any(c.unit_id >= 0 for c in u.creatable.train_locations)
        )

    found = [i for i, u in enumerate(units) if fits(u)]
    preferred = [tables.object_id(name.upper(), "ror") for name in EXAMPLES]  # what a run has, over heroes and such

    return next(
        (i for i in found if i in preferred),
        next((i for i in found if trained(units[i])), found[0] if found else None),
    )


def _reads(command: tuple, data: DatFile) -> list[Read]:
    kind, a, b, c, d = command

    if kind in (SET_ATTRIBUTE, ADD_ATTRIBUTE, MUL_ATTRIBUTE):
        damage, amount = -1, d

        if c in (ARMOUR, ATTACK) and kind == ADD_ATTRIBUTE:
            damage, amount = int(d) // 256, int(d) % 256

        unit = a if a >= 0 else _example(data, b, c, damage)

        if unit is None:
            return []

        op = {SET_ATTRIBUTE: "set", ADD_ATTRIBUTE: "add", MUL_ATTRIBUTE: "mul"}[kind]

        if c == COST:  # every cost the unit has
            costs = data.civs[1].units[unit].creatable.resource_costs if data.civs[1].units[unit].creatable else ()
            slots = [slot for slot, cost in zip(COST_SLOTS, costs, strict=False) if cost.type >= 0 and cost.amount]
            return [Read("object", (unit, slot, -1), op, amount, command) for slot in slots]

        return [Read("object", (unit, c, damage), op, amount, command)]

    if kind == RESOURCE:
        return [Read("resource", (a,), "set" if b == SET else "add", d, command)]

    if kind == MUL_RESOURCE:
        return [Read("resource", (a,), "mul", d, command)]

    if kind == TECH_COST:
        return [Read("tech", (a, TECH_COST_ATTRIBUTE, b), "set" if c == SET else "add", d, command)]

    if kind == TECH_TIME:
        return [Read("tech", (a, TECH_TIME_ATTRIBUTE, 0), "set" if c == SET else "add", d, command)]

    return []


@dataclass(frozen=True)
class Step:
    boon: Boon
    tier: Tier
    key: str
    reads: tuple[Read, ...]
    player: int = 0

    @property
    def shown(self) -> list[int]:
        """The units to place: those whose values it reads, the boon's own first."""
        return list(dict.fromkeys(r.args[0] for r in self.reads if r.kind == "object"))[:SHOWN]

    @property
    def title(self) -> str:
        return f"{self.boon.civ.value.title()} {self.boon.number} {self.tier.title}"


def _affected(step: Step, data: DatFile) -> set[tuple]:
    """Every (unit, attribute, class) its commands change (a class command changes every unit of the class), and every
    tech cost or time: cuts are added from the base cost, so two on a player go below 0 and stop there."""
    units = data.civs[PLAYER_CIV].units
    found = set()

    for r in step.reads:
        if r.kind == "object":
            unit, unit_class = r.command[1], r.command[2]
            ids = [unit] if unit >= 0 else [i for i, u in enumerate(units) if u and u.class_ == unit_class]
            found |= {(i, *r.args[1:]) for i in ids}
        elif r.kind == "tech":
            found.add(("tech", *r.args))

    return found


def assign(steps: list[Step], data: DatFile) -> list[Step]:
    """Each step to a player of TIER_PLAYERS where nothing already there changes a value its labels show, or shows a
    value it changes; a step with no such player left is left out (stacked tiers cut the same tech's cost and time
    many times over)."""
    taken = {p: (set(), set()) for p in TIER_PLAYERS}  # player -> (changed, shown)
    placed = []

    for step in steps:
        changed = _affected(step, data)
        shown = {r.args for r in step.reads if r.kind == "object"} | {
            ("tech", *r.args) for r in step.reads if r.kind == "tech"
        }
        player = next((p for p, (c, s) in taken.items() if not (c & shown) and not (s & changed)), None)

        if player is None:
            continue  # no player left without an overlap: left out (its boon's other steps are checked)

        taken[player][0].update(changed)
        taken[player][1].update(shown)
        placed.append(Step(step.boon, step.tier, step.key, step.reads, player))

    return placed


def plan(data: DatFile, techs: dict[str, int]) -> list[Step]:
    """Every tier tech in the data mod, in research order, with its reads and player: each boon's distinct steps once
    (a repeated step compiles to the same commands, and every step of a boon on one map ran out of players)."""
    steps = []

    for boon in catalogue.ALL:
        seen = set()

        for tier in sorted(boon.steps):
            key = boon_techs.key(boon, tier)
            compiled = tuple(commands(boon, tier, data)) if key in techs else ()

            if compiled and compiled not in seen:
                seen.add(compiled)
                reads = tuple(r for command in compiled for r in _reads(command, data))
                steps.append(Step(boon, tier, key, reads))

    return assign(steps, data)


def base(data: DatFile, read: Read) -> float | None:
    """A unit value before any boon: the player's civ's, from the data file. None if it's not one we know."""
    unit = data.civs[PLAYER_CIV].units[read.args[0]]
    attribute, damage = read.args[1], read.args[2]
    t50 = unit.type_50
    costs = unit.creatable.resource_costs if unit.creatable else ()
    simple = {
        0: unit.hit_points,
        1: unit.line_of_sight,
        5: unit.speed,
        10: t50.reload_time if t50 else None,
        12: t50.max_range if t50 else None,
        13: unit.bird.work_rate if unit.bird else None,
        14: unit.resource_capacity,
        21: unit.resource_storages[0].amount if unit.resource_storages else None,
        101: unit.creatable.train_locations[0].train_time
        if unit.creatable and unit.creatable.train_locations
        else None,
        103: next((c.amount for c in costs if c.type == 0), 0),
        104: next((c.amount for c in costs if c.type == 1), 0),
    }

    if attribute in COST_SLOTS:
        slot = COST_SLOTS.index(attribute)
        return costs[slot].amount if slot < len(costs) else None

    if attribute in (ARMOUR, ATTACK) and t50:
        found = t50.armours if attribute == ARMOUR else t50.attacks
        return next((a.amount for a in found if a.class_ == damage), None)

    return simple.get(attribute)


def _number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def label(step: Step, unit: int, data: DatFile) -> str:
    """What a placed unit should now be: "HP 25 -> 30" per value read on it, a line each."""
    lines = []

    for r in step.reads:
        if r.kind == "object" and r.args[0] == unit:
            before = base(data, r)
            change = f"{_number(before)} -> {_number(r.expected(before))}" if before is not None else r.op
            lines.append(f"{r.label} {change}")

    return "\n".join(lines)


def _write(step: int, marker: int, reads: tuple[Read, ...], player: int) -> list[str]:
    lines = [f"    xsWriteInt({marker});", f"    xsWriteInt({step});"]

    return lines + [f"    xsWriteFloat({r.xs(player)});" for r in reads]


def xs(steps: list[Step], techs: dict[str, int]) -> str:
    functions, dispatch = [], []

    for k, step in enumerate(steps):
        body = []

        if k:
            previous = steps[k - 1]
            body += _write(k - 1, AFTER, previous.reads, previous.player)

        body += _write(k, BEFORE, step.reads, step.player)
        body.append(f"    xsResearchTechnology({techs[step.key]}, true, false, {step.player});")
        functions.append(f"void crucibleBoonStep{k}() {{\n" + "\n".join(body) + "\n}\n")
        dispatch.append(f"    if (crucibleBoonStepAt == {k}) {{\n        crucibleBoonStep{k}();\n    }}")

    last = steps[-1]
    finish = "\n".join(_write(len(steps) - 1, AFTER, last.reads, last.player))

    return f"""// ---- crucible check: boons ----
int crucibleBoonStepAt = 0;

{"".join(functions)}
void crucibleBoonFinish() {{
{finish}
    xsWriteInt({DONE});
}}

rule crucibleBoonCheck
    active
    highFrequency
{{
    if (xsGetTime() < 2) {{
        return;
    }}

    xsCreateFile(crucibleBoonStepAt > 0);
{chr(10).join(dispatch)}
    if (crucibleBoonStepAt == {len(steps)}) {{
        crucibleBoonFinish();
        xsChatData("Boons checked: %d tier techs", {len(steps)});
        xsDisableSelf();
    }}
    xsCloseFile();
    crucibleBoonStepAt = crucibleBoonStepAt + 1;
}}
"""


def places(steps: list[Step]) -> dict[int, tuple[int, int]]:
    """Where each shown step's row starts, by step index: rows down a column, then the next column."""
    rows = (SIZE - TOP - ROW) // ROW
    shown = [k for k, s in enumerate(steps) if s.shown]

    if len(shown) > rows * ((SIZE - 4) // COLUMN):
        raise ValueError(f"{len(shown)} rows don't fit a {SIZE} map")

    return {k: (4 + (n // rows) * COLUMN, TOP + (n % rows) * ROW) for n, k in enumerate(shown)}


def setup(o, ctx, techs: dict[str, int], top: int) -> str:
    from aoe2ed.tools.world import diplomacy_set

    from crucible.datamod.mod import source_dat
    from crucible.scenarios.check import add_unit

    data = source_dat()
    steps = plan(data, techs)

    for player in range(1, PLAYERS + 1):  # no fighting
        diplomacy_set(o.handle, player, [p for p in range(1, PLAYERS + 1) if p != player], "ALLY")

    for k, (x, y) in places(steps).items():
        step, effects = steps[k], []

        for n, unit in enumerate(step.shown):
            ref = o.scenario.unit_manager.add_unit(
                player=step.player,
                unit_const=unit,
                x=x + n * CELL + 0.5,
                y=y + 0.5,
            ).reference_id
            text = label(step, unit, data)
            where = {"source_player": step.player, "selected_object_ids": [ref]}
            effects += [
                {"type": "change_object_caption", "message": f"{step.title}\n{text}", **where},
                {"type": "change_object_name", "message": f"{step.title}: {text.replace(chr(10), ', ')}", **where},
            ]

        ctx.trigger(f"Boons: label {step.key}", [], effects)

    for player in TIER_PLAYERS:  # a player with no units gets a town
        if not any(s.player == player and s.shown for s in steps):
            add_unit(o.scenario, "house", SIZE - 6, 4 + 3 * player, player=player)

    ctx.xs(xs(steps, techs))
    reads = sum(len(s.reads) for s in steps)
    shown = sum(len(s.shown) for s in steps)

    return (
        f'BOONS: {len(steps)} tier techs are researched in the first seconds (wait for "Boons checked" in the '
        f'chat). {shown} units show what their tier should do: the label over each unit and its name say "before '
        f"-> after\"; click it to compare. Each tier's units belong to one player (colours), so tiers never mix. "
        f"Costs, work rates, research times and resources ({reads} values in all) are in the log: quit, then run "
        f"`crucible check --test boons --report`."
    )


def read(sizes: dict[int, int], path: Path | None = None) -> dict:
    """Step -> BEFORE/AFTER -> the values read (`sizes`: how many each step reads); "done" once it finished."""
    path = path or paths().profile / "profile" / FILE
    data, at, found = path.read_bytes(), 0, {}

    def take(fmt: str):
        nonlocal at
        (value,) = struct.unpack_from(fmt, data, at)
        at += 4
        return value

    while at < len(data):
        marker = take("<i")

        if marker == DONE:
            found["done"] = True
            break

        step = take("<i")
        found.setdefault(step, {})[marker] = [take("<f") for _ in range(sizes[step])]

    return found


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(0.51, abs(b) * 0.01)


def report(techs: dict[str, int], path: Path | None = None) -> list[str]:
    """What didn't come out as expected, one line each; empty if everything did."""
    from crucible.datamod.mod import source_dat

    data = source_dat()
    steps = plan(data, techs)
    found = read({k: len(s.reads) for k, s in enumerate(steps)}, path)
    lines = [] if found.get("done") else ["the check didn't finish"]

    for k, step in enumerate(steps):
        values = found.get(k, {})

        if BEFORE not in values or AFTER not in values:
            lines.append(f"{step.key}: not read")
            continue

        for r, before, after in zip(step.reads, values[BEFORE], values[AFTER], strict=True):
            where = f"{step.key} (player {step.player}) {r.kind} {r.args}"
            want = r.expected(before)

            if not _close(after, want):
                lines.append(f"{where}: {before:g} -> {after:g}, expected {want:g} ({r.op} {r.amount:g})")

            if r.kind == "object" and r.args[0] in step.shown:
                label_before = base(data, r)

                if label_before is not None and not _close(before, label_before):
                    lines.append(f"{where}: the label says it was {label_before:g}, the game read {before:g}")

    return lines
