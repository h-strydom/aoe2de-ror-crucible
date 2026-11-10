"""What a modifier changes, as the data file addresses it: (unit, class) selectors and tech ids.

The classes and unit ids are the ones RoR's own civ bonuses use (its Tech. Tree and Team Bonus effects).
"""

from aoe2ed import tables
from genieutils.datfile import DatFile

from crucible.bonuses.model import Group, Modifier

UPGRADE_UNIT, BUILDING = 3, 80  # effect command type; unit type
Selector = tuple[int, int]  # an effect command's (a, b): a unit id with class -1, or unit -1 with a class

CLASSES: dict[Group, tuple[int, ...]] = {
    Group.ARCHERS: (0, 36),
    Group.CAVALRY: (12,),
    Group.INFANTRY: (6,),
    Group.PRIESTS: (18,),
    Group.SHIPS: (22, 2, 21, 20),  # war, trade, fishing, transport
    Group.SIEGE: (13, 55),
    Group.VILLAGERS: (4,),
    Group.MILITARY: (0, 6, 12, 13, 22, 23, 36, 44, 47, 55),  # Lac Viet's training bonus
    Group.NON_RANGED: (29, 6, 12, 4, 21, 2, 20),  # Macedonians' line of sight bonus
    Group.BUILDINGS: (3, 27, 39, 52),  # with walls, gates and towers (Choson's line of sight bonus)
    Group.TOWERS: (52,),
    Group.WALLS: (27, 39),  # walls and gates
}
UNITS: dict[Group, tuple[int, ...]] = {  # villager jobs: the male and female unit
    Group.FARMERS: (214, 259, 50, 1187),  # and the farms themselves, as Minoans' bonus does
    Group.FORAGERS: (120, 354),
    Group.GOLD_MINERS: (579, 581),
    Group.HUNTERS: (122, 216),
    Group.STONE_MINERS: (124, 220),
    Group.WOODCUTTERS: (123, 218),
}


def object_id(name: str) -> int:
    return tables.object_id(name.upper(), "ror")


def upgrades(data: DatFile) -> dict[int, set[int]]:
    """Unit id -> the ids it's upgraded to by any effect."""
    found: dict[int, set[int]] = {}

    for effect in data.effects:
        for command in effect.effect_commands:
            if command.type == UPGRADE_UNIT:
                found.setdefault(command.a, set()).add(command.b)

    return found


def with_ages(data: DatFile, unit: int) -> list[int]:
    """A building and the versions the ages upgrade it to (RoR's Market is 84, then 116 and 137); a unit alone,
    as its upgrades are targets of their own."""
    if data.civs[1].units[unit].type != BUILDING:
        return [unit]

    chains, found, todo = upgrades(data), [unit], [unit]

    while todo:
        for later in sorted(chains.get(todo.pop(), ())):
            if later not in found:
                found.append(later)
                todo.append(later)

    return found


def selectors(m: Modifier, data: DatFile) -> list[Selector]:
    """The targets and groups, each as the (unit, class) an effect command takes."""
    found = [(unit, -1) for target in m.targets for unit in with_ages(data, object_id(target))]

    for group in m.groups:
        if group in CLASSES:
            found += [(-1, c) for c in CLASSES[group]]
        elif group in UNITS:
            found += [(unit, -1) for unit in UNITS[group]]
        else:
            raise NotImplementedError(f"{m.id}: {group} isn't a set of units: doesn't compile yet")

    return found


def tech_ids(m: Modifier) -> list[int]:
    return [tables.tech_id(tech.upper(), "ror") for tech in m.techs]
