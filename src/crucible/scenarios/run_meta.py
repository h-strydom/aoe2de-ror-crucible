"""The meta upgrades in crucible_run: loaded from the campaign bank at the start, each level giving the player one
more of something (meta.py). Outside the Crucible campaign nothing is loaded, so a standalone run gets none.

Buildings kept come from the base the Allies were handed, nearest the Town Center first; they change hands before
the Allies' buildings drop to 1 HP (run_xs waits for it).

Starting soldiers stand in slots by the Wonder, placed by hand (2026-11-17): meta upgrades will improve how many and
which units fill them. For now the Clubmen upgrade fills the first three melee slots.
"""

from math import dist

from aoe2ed import blocks

from crucible import meta

VILLAGER_MALE, VILLAGER_FEMALE = 83, 293
HOUSE, GRANARY, STORAGE_PIT, CLUBMAN = 70, 68, 562, 281
LOOKS_ONLY = (HOUSE,)  # kept by a change of hands (no buttons to lose); the rest are created anew
AGE_TECHS = ((1, 101), (2, 102), (3, 103))  # (the age reached, its tech): Tool, Bronze, Iron
UPGRADE_UNIT = 3  # effect command
CURRENT_AGE = 6  # resource
SLOTS = {  # where starting soldiers stand: tiles, in the order they fill
    "melee": ((104, 114), (105, 114), (105, 115), (104, 115), (103, 114)),
    "ranged": ((105, 117), (105, 118), (104, 118), (104, 117), (103, 118)),
    "scout": ((105, 120),),
    "cavalry": ((103, 120), (103, 121), (103, 122)),
    "siege": ((102, 116),),
}
KEPT = {  # upgrade -> the building type each level keeps
    meta.HOUSES.key: HOUSE,
    meta.GRANARY.key: GRANARY,
    meta.STORAGE_PIT.key: STORAGE_PIT,
    meta.BARRACKS_UPGRADE.key: meta.BARRACKS,
}


def _at_least(key: str, level: int) -> list[dict]:
    return [{"type": "variable_value", "variable": key, "comparison": "LARGER_OR_EQUAL", "quantity": level}]


def age_chains(data) -> dict[int, dict[int, int]]:
    """A building's Age1 unit -> the unit each age makes it ({1: Age2, 2: Age3, 3: Age4}), read from the age techs
    (ids aren't in age order: the Barracks is 12, 498, 132)."""
    chains: dict[int, dict[int, int]] = {}

    for age, tech in AGE_TECHS:
        for command in data.effects[data.techs[tech].effect_id].effect_commands:
            if command.type == UPGRADE_UNIT:
                chains.setdefault(command.a, {})[age] = command.b

    return chains


def _keep(ctx, name: str, conditions: list[dict], unit, allies: int, player: int) -> None:
    """Make one of the Allies' buildings the player's. A building given to a player keeps the look of the age it had
    (AoE's rule), so a working one (Barracks, Granary, Storage Pit) is removed and, a second later (in the same moment
    the tile still counted as taken: the Granary never came back), created anew for the player on its tile, to age up
    like one the player built. (Replacing it with the next age's unit lost its buttons: units train at the Age1
    Barracks, 12, not at the Age2 one.) A house only looks, so it changes hands and _ages replaces it at each age."""
    if unit.unit_const in LOOKS_ONLY:
        move = {
            "type": "change_ownership",
            "source_player": allies,
            "target_player": player,
            "selected_object_ids": [unit.reference_id],
        }
        ctx.trigger(name, conditions, [move])

        return

    placed = f"{name} placed"
    remove = {"type": "remove_object", "source_player": allies, "selected_object_ids": [unit.reference_id]}
    create = {
        "type": "create_object",
        "object_list_unit_id": unit.unit_const,
        "source_player": player,
        "location": [int(unit.x), int(unit.y)],
    }
    later = {"type": "activate_trigger", "trigger_id": placed}
    ctx.triggers(
        {"name": name, "conditions": conditions, "effects": [remove, later]},
        {"name": placed, "enabled": False, "conditions": [{"type": "timer", "timer": 1}], "effects": [create]},
    )


def _ages(ctx, kept: list, chains: dict[int, dict[int, int]], player: int) -> None:
    """At each age the player reaches, each kept house is replaced, on its own tile, by that age's."""
    for age, _ in AGE_TECHS:
        effects = []

        for unit in kept:
            chain = {0: unit.unit_const, **chains.get(unit.unit_const, {})}
            before = max((a for a in chain if a < age), default=0)

            if age in chain:
                tile = [int(unit.x), int(unit.y), int(unit.x), int(unit.y)]
                effects.append(
                    {
                        "type": "replace_object",
                        "source_player": player,
                        "target_player": player,
                        "object_list_unit_id": chain[before],
                        "object_list_unit_id_2": chain[age],
                        "area": tile,
                    }
                )

        ctx.trigger(
            f"Meta: kept buildings to age {age}",
            [{"type": "accumulate_attribute", "source_player": player, "attribute": CURRENT_AGE, "quantity": age}],
            effects,
        )


def add(
    ctx,
    s,
    *,
    player: int,
    allies: int,
    town_center: tuple[float, float],
    villagers,
    chains: dict[int, dict[int, int]],
) -> None:
    """`villagers`: where each extra villager starts (tile centres), in order. `chains`: age_chains()."""
    blocks.bank.load(ctx, {upgrade.key: 0 for upgrade in meta.UPGRADES}, name="Meta: load upgrades")

    for level, (x, y) in enumerate(villagers[: meta.VILLAGERS.levels], start=1):
        unit = VILLAGER_MALE if level % 2 else VILLAGER_FEMALE
        ctx.trigger(
            f"Meta: villager {level}",
            _at_least(meta.VILLAGERS.key, level),
            [
                {
                    "type": "create_object",
                    "object_list_unit_id": unit,
                    "source_player": player,
                    "location": [int(x), int(y)],
                }
            ],
        )

    kept = []

    for key, building in KEPT.items():
        upgrade = next(u for u in meta.UPGRADES if u.key == key)
        candidates = sorted(
            (u for u in s.unit_manager.units[allies] if u.unit_const == building),
            key=lambda u: dist((u.x, u.y), town_center),
        )
        if building in LOOKS_ONLY:
            kept += candidates[: upgrade.levels]

        for level, unit in enumerate(candidates[: upgrade.levels], start=1):
            _keep(ctx, f"Meta: {upgrade.title} {level}", _at_least(key, level), unit, allies, player)

    _ages(ctx, kept, chains, player)
    clubmen = [
        {"type": "create_object", "object_list_unit_id": CLUBMAN, "source_player": player, "location": list(tile)}
        for tile in SLOTS["melee"][: meta.CLUBMEN_PER_LEVEL]
    ]
    ctx.trigger("Meta: Clubmen", _at_least(meta.CLUBMEN.key, 1), clubmen)
