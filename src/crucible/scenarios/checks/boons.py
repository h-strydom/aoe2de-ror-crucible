"""Test: every tier of every boon (crucible.boons) does what it compiles to, read back from the game.

Each boon's tiers go to players 1, 2 and 3 in turn (its first tier to player 1, ...), so a boon's tiers don't stack.
XS researches one tier tech at a time and reads every value its commands change, just before and just after (the
after read waits a tick), writing both to crucible_check.xsdat; report() compares each after with what the command
should make of the before. Nothing to watch: start the map, wait for "Boons checked" in the chat, then run the report.

Reads (plan()): a unit attribute on the unit, or one unit of the class (xsGetObjectAttribute; armour and attack by
class); a player resource (xsPlayerAttribute); a tech's cost or research time (xsGetTechAttribute). Costs are read
per cost slot (Amount First, Second, Third Cost). Other command types aren't read.
"""

import struct
from dataclasses import dataclass
from pathlib import Path

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

NAME = "boons"
BOONS: tuple[str, ...] = ()  # the old modifiers: none
BUTTONS: dict[str, int] = {}
PLAYERS = max(len(b.tiers) for b in catalogue.ALL)
FILE = "crucible_check.xsdat"
BEFORE, AFTER, DONE = 1, 2, 9
COST_SLOTS = (174, 175, 176)  # Amount First, Second, Third Cost
TECH_COST_ATTRIBUTE, TECH_TIME_ATTRIBUTE = 1, 2  # cTechCost, cTechResearchTime (the XS prelude's values)


def datamod(mod) -> None:
    boon_techs.add(mod)


@dataclass(frozen=True)
class Read:
    """One value to read: kind "object" (unit, attribute, class), "resource" (resource) or "tech" (tech,
    attribute, cost type); and what the command should make of it."""

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

    def trained(u) -> bool:
        return bool(u.creatable and any(c.unit_id >= 0 for c in u.creatable.train_locations))

    found = [i for i, u in enumerate(units) if fits(u)]

    return next((i for i in found if trained(units[i])), found[0] if found else None)


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
        return [Read("tech", (a, TECH_TIME_ATTRIBUTE, -1), "set" if c == SET else "add", d, command)]

    return []


@dataclass(frozen=True)
class Step:
    boon: Boon
    tier: Tier
    player: int
    key: str
    reads: tuple[Read, ...]


def plan(data: DatFile, techs: dict[str, int]) -> list[Step]:
    """Every tier tech in the data mod, in research order, with its reads."""
    steps = []

    for boon in catalogue.ALL:
        for slot, tier in enumerate(sorted(boon.tiers)):
            key = boon_techs.key(boon, tier)

            if key in techs:
                reads = tuple(r for command in commands(boon, tier, data) for r in _reads(command, data))
                steps.append(Step(boon, tier, slot + 1, key, reads))

    return steps


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


def setup(o, ctx, techs: dict[str, int], top: int) -> str:
    from crucible.datamod.mod import source_dat
    from crucible.scenarios.check import add_unit

    steps = plan(source_dat(), techs)

    for player in range(2, PLAYERS + 1):
        add_unit(o.scenario, "house", 50, top + 2 * player, player=player)  # a player with no units gets a town

    ctx.xs(xs(steps, techs))
    reads = sum(len(s.reads) for s in steps)

    return (
        f"BOONS: {len(steps)} tier techs ({reads} values) are researched one at a time, each boon's tiers by players "
        "1 to 3. Nothing to do: wait for \"Boons checked\" in the chat (a few seconds), then quit."
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


def report(techs: dict[str, int], path: Path | None = None) -> list[str]:
    """What didn't come out as expected, one line each; empty if everything did."""
    from crucible.datamod.mod import source_dat

    steps = plan(source_dat(), techs)
    found = read({k: len(s.reads) for k, s in enumerate(steps)}, path)
    lines = [] if found.get("done") else ["the check didn't finish"]

    for k, step in enumerate(steps):
        values = found.get(k, {})

        if BEFORE not in values or AFTER not in values:
            lines.append(f"{step.key}: not read")
            continue

        for r, before, after in zip(step.reads, values[BEFORE], values[AFTER], strict=True):
            want = r.expected(before)

            if abs(after - want) > max(0.51, abs(want) * 0.01):
                lines.append(
                    f"{step.key} (player {step.player}) {r.kind} {r.args}: {before:g} -> {after:g}, expected "
                    f"{want:g} ({r.op} {r.amount:g})"
                )

    return lines
