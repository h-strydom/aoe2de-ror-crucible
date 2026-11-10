"""Modifiers to game effect commands: (type, a, b, c, d) as in the data file's effects.

Each modifier becomes a hidden tech in the data mod whose effect is these commands, so handing a bonus to anyone
is one thing: research its tech. Only the stats below compile so far; the rest raise until they're needed.
"""

from aoe2ed import tables

from crucible.bonuses.model import Mode, Modifier, Stat

Command = tuple[int, int, int, int, float]

SET_ATTRIBUTE, RESOURCE, ADD_ATTRIBUTE, MUL_ATTRIBUTE = 0, 1, 4, 5  # effect command types
ATTRIBUTES = {Stat.HP: 0, Stat.SPEED: 5, Stat.WORK_RATE: 13}  # unit attributes
FOOD, WOOD, STONE, GOLD = 0, 1, 2, 3
ADD = 1  # resource modifier mode


def object_id(name: str) -> int:
    return tables.object_id(name.upper(), "ror")


def commands(m: Modifier) -> list[Command]:
    if m.groups or m.techs:
        raise NotImplementedError(f"{m.id}: groups and techs: doesn't compile yet")

    if m.stat in ATTRIBUTES:
        attribute = ATTRIBUTES[m.stat]
        if m.change.mode is Mode.PERCENT:
            return [(MUL_ATTRIBUTE, object_id(t), -1, attribute, 1 + m.change.amount) for t in m.targets]
        return [(ADD_ATTRIBUTE, object_id(t), -1, attribute, m.change.amount) for t in m.targets]

    if m.stat is Stat.ALL_RESOURCES and m.change.mode is Mode.FLAT:
        return [(RESOURCE, r, ADD, -1, m.change.amount) for r in (FOOD, WOOD, STONE, GOLD)]

    raise NotImplementedError(f"{m.id}: {m.stat} ({m.change.mode}) doesn't compile yet")
