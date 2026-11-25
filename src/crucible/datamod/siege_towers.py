"""Siege towers (Zenobia's Tower in the hub, 2026-11-25): a Ballista Tower and a Catapult Tower villagers build
beside the other towers (they don't replace the Guard Tower). Each is its siege weapon in a tower: its attacks, range,
minimum range, reload, accuracy, projectile and blast come from the Ballista or the Stone Thrower, and follow that line
as it upgrades (Helepolis; Catapult, Heavy Catapult) and as siege techs and boons change it (all but its cost and
train time). As towers (class 52) they take building and tower upgrades and boons too, but not the Guard Tower's
attack and range (those come by upgrading the Watch Tower line, which they're not on).

The Granary's Catapult Tower research (RoR's Ballista Tower upgrade) no longer upgrades towers: with the hub upgrades it
lets villagers build them, once Ballistics is researched (run_meta).
"""

import copy
import itertools

from crucible.datamod.mod import DataMod

TOWER_BASE = 236  # RoR's Ballista Tower: the look, hit points and armour both start from
BUILDER = 118  # the villager's builder: where buildings are "trained"
TOWER_TECH = 2  # the Granary's Catapult Tower research (RoR's Ballista Tower upgrade)
TOWER_TECH_REQUIRES = (106, 103)  # Ballistics, the Iron Age (no Guard Tower)
SET, ADD, MULTIPLY = 0, 4, 5  # effect command types
UPGRADE_UNIT = 3
ATTACK, RELOAD, ACCURACY, RANGE, PROJECTILE, MIN_RANGE, BLAST_WIDTH, BLAST_LEVEL, LOS = 9, 10, 11, 12, 16, 20, 22, 44, 1
NOT_MIRRORED = (100, 101, 103, 104, 105, 106)  # costs and train time: siege boons' cost cuts aren't the towers'
LOS_MARGIN = 2  # tiles of sight beyond its range
ADDED = (  # (attribute, field) an upgrade adds the difference of
    (RANGE, "max_range"),
    (MIN_RANGE, "min_range"),
    (RELOAD, "reload_time"),
    (ACCURACY, "accuracy_percent"),
    (BLAST_WIDTH, "blast_width"),
)
REPLACED = ((PROJECTILE, "projectile_unit_id"), (BLAST_LEVEL, "blast_attack_level"))  # set to the new unit's


class Tower:
    def __init__(self, key: str, title: str, line: tuple[int, ...], siege_class: int, button: int, costs):
        self.key = key  # the manifest key
        self.title = title
        self.line = line  # the siege line it follows, first to last
        self.siege_class = siege_class
        self.button = button  # on the villager's build panel
        self.costs = costs  # (resource id, amount): stone 2, gold 3


TOWERS = (
    Tower("ballista_tower", "Ballista Tower", (279, 542), 55, 12, ((2, 300), (3, 100))),  # Ballista, Helepolis
    Tower("catapult_tower", "Catapult Tower", (280, 550, 588), 13, 13, ((2, 100), (3, 300))),  # Stone Thrower...
)
COPIED = (
    "attacks",
    "max_range",
    "min_range",
    "reload_time",
    "accuracy_percent",
    "accuracy_dispersion",
    "projectile_unit_id",
    "blast_width",
    "blast_attack_level",
    "blast_damage",
    "friendly_fire_damage",
    "displayed_attack",
    "displayed_range",
    "displayed_reload_time",
)


def add(mod: DataMod) -> None:
    """The towers (after buildings.add: they keep its tower counter), and the Granary research that brings them."""
    for tower in TOWERS:
        unit = mod.copy_unit(TOWER_BASE)
        mod.manifest[tower.key] = unit
        name = mod.strings.add(tower.title)
        help_id = mod.strings.add(
            f"Build <b>{tower.title}<b> (<cost>)\nA tower that shoots as your {tower.title.split()[0]} line does."
        )

        for civ in mod.data.civs:
            built, siege = civ.units[unit], civ.units[tower.line[0]]

            if built is None or siege is None:
                continue

            built.name = f"Crucible {tower.key}"
            built.enabled = 0  # a trigger switches it on (run_meta)
            built.language_dll_name = built.creatable.button_short_tooltip_id = name
            built.language_dll_help = built.creatable.button_extended_tooltip_id = help_id

            for field in COPIED:
                setattr(built.type_50, field, copy.deepcopy(getattr(siege.type_50, field)))

            built.line_of_sight = max(built.line_of_sight, siege.type_50.max_range + LOS_MARGIN)
            location = built.creatable.train_locations[0]
            location.unit_id, location.button_id = BUILDER, tower.button
            built.creatable.train_locations = [location]

            for slot, cost in enumerate(built.creatable.resource_costs):
                cost.type, cost.amount, cost.flag = (*tower.costs[slot], 1) if slot < len(tower.costs) else (-1, 0, 0)

    _upgrades(mod)
    _tower_tech(mod)


def _diff(mod: DataMod, before: int, after: int, tower: int) -> list[tuple[int, int, int, int, float]]:
    """Commands making `tower` shoot as `after` does where it shot as `before`: the differences added (so boons
    already on it stay), the projectile and blast level set."""
    a, b = mod.data.civs[1].units[before].type_50, mod.data.civs[1].units[after].type_50
    found = []
    attacks = {x.class_: x.amount for x in a.attacks}

    for x in b.attacks:
        if x.amount != attacks.get(x.class_, x.amount):
            found.append((ADD, tower, -1, ATTACK, float(x.class_ * 256 + x.amount - attacks[x.class_])))

    for attribute, field in ADDED:
        change = getattr(b, field) - getattr(a, field)

        if change:
            found.append((ADD, tower, -1, attribute, float(change)))

            if attribute == RANGE:
                found.append((ADD, tower, -1, LOS, float(change)))

    for attribute, field in REPLACED:
        if getattr(b, field) != getattr(a, field):
            found.append((SET, tower, -1, attribute, float(getattr(b, field))))

    return found


def _upgrades(mod: DataMod) -> None:
    """Each siege upgrade (Helepolis; Catapult, Heavy Catapult) upgrades its tower too."""
    for tower in TOWERS:
        unit = mod.manifest[tower.key]

        for before, after in itertools.pairwise(tower.line):
            for tech in mod.data.techs:
                if tech.effect_id < 0:
                    continue

                effect = mod.data.effects[tech.effect_id]

                if any(c.type == UPGRADE_UNIT and c.a == before and c.b == after for c in effect.effect_commands):
                    _append(mod, effect, _diff(mod, before, after, unit))


def _append(mod: DataMod, effect, commands) -> None:
    template = effect.effect_commands[0]

    for kind, a, b, c, d in commands:
        command = copy.deepcopy(template)
        command.type, command.a, command.b, command.c, command.d = kind, a, b, c, d
        effect.effect_commands.append(command)


def _tower_tech(mod: DataMod) -> None:
    """The Granary's Catapult Tower research: no tower upgrades, Ballistics and the Iron Age needed (triggers say what
    it brings)."""
    tech = mod.data.techs[TOWER_TECH]
    tech.effect_id = mod.new_effect("Crucible siege towers", [])
    tech.required_techs = (*TOWER_TECH_REQUIRES, *(-1,) * (6 - len(TOWER_TECH_REQUIRES)))
    tech.required_tech_count = len(TOWER_TECH_REQUIRES)
    tech.language_dll_description = mod.strings.add("Research Siege Towers")
    tech.language_dll_help = tech.language_dll_tech_tree = mod.strings.add(
        "Research <b>Siege Towers<b> (<cost>)\nVillagers can build the Ballista and Catapult Towers your hub upgrades "
        "brought."
    )


def mirror(mod: DataMod) -> None:
    """Every change to a tower's siege line (by unit or by class: techs, boons, bonuses), its cost and train time
    left out, made to the tower too. Last: after every part has added its techs."""
    targets = []

    for tower in TOWERS:
        unit = mod.manifest[tower.key]
        targets += [(("unit", u), unit) for u in tower.line] + [(("class", tower.siege_class), unit)]

    by_target = dict(targets)

    for effect in mod.data.effects:
        found = []

        for c in effect.effect_commands:
            if c.type not in (SET, ADD, MULTIPLY) or c.c in NOT_MIRRORED:
                continue

            key = ("unit", c.a) if c.a >= 0 else ("class", c.b)

            mirrored = (c.type, by_target.get(key, -1), -1, c.c, c.d)

            # once a tower: a tech often changes each unit of the line alike (Alchemy, boons), +1 three times else
            if key in by_target and mirrored not in found:
                found.append(mirrored)

        if found:
            _append(mod, effect, found)
