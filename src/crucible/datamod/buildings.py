"""Buildings the run needs changed in RoR's data: Town Centers and towers counted. Each adds 1 to a spare player
resource while it stands (a second resource storage, as each House adds to 51), so a population room boon reaches
those already built (bonuses' population).
"""

from crucible.bonuses.compile.stats import COUNTED_CLASSES, COUNTED_UNITS, HOUSE_COUNT
from crucible.datamod.mod import DataMod

BUILDING = 80  # unit type
STANDING = 4  # storage mode: given on completion, taken back on death


def _count(unit, resource: int) -> None:
    storages = unit.resource_storages

    if any(s.type == resource for s in storages):
        return

    free = next(s for s in storages if s.type < 0)
    free.type, free.amount, free.flag = resource, 1.0, STANDING


def counters(mod: DataMod) -> None:
    for civ in mod.data.civs:
        for i, unit in enumerate(civ.units):
            if unit is None or unit.type != BUILDING:
                continue

            resource = COUNTED_UNITS.get(i, COUNTED_CLASSES.get(unit.class_))

            if resource is not None and resource != HOUSE_COUNT:  # houses count themselves
                _count(unit, resource)


def add(mod: DataMod) -> None:
    counters(mod)
