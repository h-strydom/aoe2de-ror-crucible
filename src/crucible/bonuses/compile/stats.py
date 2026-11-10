"""How each stat compiles: effect commands (type, a, b, c, d), copying how RoR's own civ bonuses do it."""

from collections.abc import Callable

from genieutils.datfile import DatFile

from crucible.bonuses.compile.targets import Selector, selectors, tech_ids
from crucible.bonuses.model import Group, Mode, Modifier, Stat

Command = tuple[int, int, int, int, float]

SET_ATTRIBUTE, RESOURCE, ADD_ATTRIBUTE, MUL_ATTRIBUTE, MUL_RESOURCE = 0, 1, 4, 5, 6  # effect command types
TECH_COST, TECH_TIME = 101, 103
SET, ADD = 0, 1  # resource and tech modifier modes
FOOD, WOOD, STONE, GOLD = 0, 1, 2, 3
PIERCE, MELEE = 3, 4  # armour and attack classes

# unit attributes
HP, LINE_OF_SIGHT, SPEED, ARMOUR, ATTACK, RELOAD, RANGE, WORK_RATE, CARRY = 0, 1, 5, 8, 9, 10, 12, 13, 14
STORAGE = 21  # amount of the first resource storage: population room on houses, town centres and towers
COST, TRAIN_TIME, FOOD_COST, WOOD_COST = 100, 101, 103, 104

# player resources
FARM_FOOD, TRIBUTE_TAX, CONVERSION_RESISTANCE, RESEARCH_TIME, HEAL_RATE, CONSTRUCTION_RATE = 36, 46, 77, 86, 89, 195


def _flat_only(m: Modifier) -> None:
    if m.change.mode is not Mode.FLAT:
        raise NotImplementedError(f"{m.id}: {m.stat} ({m.change.mode}) doesn't compile yet")


def _attribute(attribute: int, *, faster: bool = False) -> Callable[[Modifier, DatFile], list[Command]]:
    """A unit attribute on every target: +x% multiplies it (by 1/(1+x) when lower is `faster`, like reload or
    training time); +x adds."""

    def compile_(m: Modifier, data: DatFile) -> list[Command]:
        if m.change.mode is Mode.PERCENT:
            factor = 1 / (1 + m.change.amount) if faster else 1 + m.change.amount
            return [(MUL_ATTRIBUTE, unit, cls, attribute, round(factor, 4)) for unit, cls in selectors(m, data)]

        return [(ADD_ATTRIBUTE, unit, cls, attribute, m.change.amount) for unit, cls in selectors(m, data)]

    return compile_


def _armour(armour_class: int) -> Callable[[Modifier, DatFile], list[Command]]:
    def compile_(m: Modifier, data: DatFile) -> list[Command]:
        _flat_only(m)
        value = armour_class * 256 + m.change.amount
        return [(ADD_ATTRIBUTE, unit, cls, ARMOUR, value) for unit, cls in selectors(m, data)]

    return compile_


def _resource(resource: int, *, mode: int | None = None, faster: bool = False):
    """A player resource: +x% multiplies it (or sets it to 1+x with mode SET); +x adds."""

    def compile_(m: Modifier, data: DatFile) -> list[Command]:
        if m.change.mode is Mode.FLAT:
            return [(RESOURCE, resource, ADD, -1, m.change.amount)]

        factor = round(1 / (1 + m.change.amount) if faster else 1 + m.change.amount, 4)

        if mode == SET:
            return [(RESOURCE, resource, SET, -1, factor)]

        return [(MUL_RESOURCE, resource, -1, -1, factor)]

    return compile_


def _attacks(data: DatFile, selector: Selector) -> list[tuple[int, int]]:
    """(class, amount) of a unit's attacks, or of the first armed unit of a class."""
    unit_id, unit_class = selector
    units = data.civs[1].units

    if unit_id >= 0:
        candidates = [units[unit_id]]
    else:
        candidates = [u for u in units if u and u.class_ == unit_class and u.type_50 and u.type_50.attacks]

    for unit in candidates:
        if unit and unit.type_50 and unit.type_50.attacks:
            return [(a.class_, a.amount) for a in unit.type_50.attacks]

    raise ValueError(f"no attacks for {selector}")


def attack(m: Modifier, data: DatFile) -> list[Command]:
    """+x adds to each target's main attack class; +x% adds x% of each of its attacks."""
    found = []

    for selector in selectors(m, data):
        attacks = _attacks(data, selector)

        if m.change.mode is Mode.FLAT:
            main = max(attacks, key=lambda a: a[1])[0]
            changes = [(main, m.change.amount)]
        else:
            changes = [(cls, max(1, round(amount * m.change.amount))) for cls, amount in attacks if amount > 0]

        found += [(ADD_ATTRIBUTE, *selector, ATTACK, cls * 256 + amount) for cls, amount in changes]

    return found


def range_(m: Modifier, data: DatFile) -> list[Command]:
    """Range, and line of sight by as much (as Choson's tower bonus does)."""
    _flat_only(m)
    return [
        (ADD_ATTRIBUTE, unit, cls, attribute, m.change.amount)
        for unit, cls in selectors(m, data)
        for attribute in (RANGE, LINE_OF_SIGHT)
    ]


def tech_cost(m: Modifier, data: DatFile) -> list[Command]:
    """-x% of each cost of each tech; -100% sets them to 0."""
    found = []

    for tech in tech_ids(m):
        for cost in data.techs[tech].resource_costs:
            if cost.type < 0:
                continue

            if m.change.amount <= -1:
                found.append((TECH_COST, tech, cost.type, SET, 0))
            else:
                found.append((TECH_COST, tech, cost.type, ADD, round(cost.amount * m.change.amount)))

    return found


def cost(m: Modifier, data: DatFile) -> list[Command]:
    if m.techs:
        return tech_cost(m, data)

    return _attribute(COST)(m, data)


def research_time(m: Modifier, data: DatFile) -> list[Command]:
    found = []

    for tech in tech_ids(m):
        time = data.techs[tech].research_locations[0].research_time
        found.append((TECH_TIME, tech, 1, ADD, round(time * m.change.amount)))

    return found


def work_rate(m: Modifier, data: DatFile) -> list[Command]:
    """Builders work faster through the player's construction rate (as Babylonians' bonus does)."""
    if Group.BUILDERS in m.groups:
        return _resource(CONSTRUCTION_RATE)(m, data)

    return _attribute(WORK_RATE)(m, data)


def all_resources(m: Modifier, data: DatFile) -> list[Command]:
    _flat_only(m)
    return [(RESOURCE, r, ADD, -1, m.change.amount) for r in (FOOD, WOOD, STONE, GOLD)]


COMPILERS: dict[Stat, Callable[[Modifier, DatFile], list[Command]]] = {
    Stat.HP: _attribute(HP),
    Stat.ATTACK: attack,
    Stat.ATTACK_SPEED: _attribute(RELOAD, faster=True),
    Stat.MELEE_ARMOUR: _armour(MELEE),
    Stat.PIERCE_ARMOUR: _armour(PIERCE),
    Stat.RANGE: range_,
    Stat.SPEED: _attribute(SPEED),
    Stat.LINE_OF_SIGHT: _attribute(LINE_OF_SIGHT),
    Stat.WORK_RATE: work_rate,
    Stat.CARRY: _attribute(CARRY),
    Stat.COST: cost,
    Stat.FOOD_COST: _attribute(FOOD_COST),
    Stat.WOOD_COST: _attribute(WOOD_COST),
    Stat.TRAINING_SPEED: _attribute(TRAIN_TIME, faster=True),
    Stat.BUILD_SPEED: _attribute(TRAIN_TIME, faster=True),  # a building's train time is its build time
    Stat.RESEARCH_SPEED: _resource(RESEARCH_TIME, mode=SET, faster=True),  # set, as Palmyrans do; multiplying fails
    Stat.RESEARCH_TIME: research_time,
    Stat.HEAL_SPEED: _resource(HEAL_RATE),
    Stat.REJUVENATION: _attribute(RELOAD),  # a priest's faith recharge is its reload attribute, higher is faster
    Stat.CONVERSION_RESISTANCE: _resource(CONVERSION_RESISTANCE, mode=SET),
    Stat.POPULATION: _attribute(STORAGE),
    Stat.FOOD: _resource(FARM_FOOD),
    Stat.ALL_RESOURCES: all_resources,
    Stat.STARTING_FOOD: _resource(FOOD),
    Stat.TRADE_GOLD: _attribute(WORK_RATE),  # unverified: a trade boat's work rate as its trade rate
    Stat.TRIBUTE_TAX: _resource(TRIBUTE_TAX),
}
