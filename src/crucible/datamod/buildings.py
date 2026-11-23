"""Buildings the run needs changed in RoR's data.

- Town Centers counted: each Town Center and tower adds 1 to a spare player resource while it stands (a second resource
  storage, as each House adds to 51), so a population room boon reaches those already built (bonuses' population).
- Town Centers buildable: RoR has no button for them; they go on the villager's economic page (button 5, free) at
  RoR's own cost and time (200 wood, 60 s), still disabled: the run enables them from the Bronze Age (run_rules).
"""

from crucible.bonuses.compile.stats import COUNTED_CLASSES, COUNTED_UNITS, HOUSE_COUNT
from crucible.datamod.mod import DataMod

BUILDING = 80  # unit type
STANDING = 4  # storage mode: given on completion, taken back on death
BUILDER = 118  # the villager's build "location"
TOWN_CENTER, TOWN_CENTER_BUTTON = 109, 5


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


def town_centers(mod: DataMod) -> None:
    for civ in mod.data.civs:
        unit = civ.units[TOWN_CENTER]

        if unit is None:
            continue

        place = unit.creatable.train_locations[0]
        place.unit_id, place.button_id = BUILDER, TOWN_CENTER_BUTTON


def add(mod: DataMod) -> None:
    counters(mod)
    town_centers(mod)
