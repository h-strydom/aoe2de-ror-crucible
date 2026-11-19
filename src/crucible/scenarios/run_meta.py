"""The meta upgrades in crucible_run: loaded from the campaign bank at the start, each level giving the player one
more of something (meta.py). Outside the Crucible campaign nothing is loaded, so a standalone run gets none.

Buildings kept come from the base the Allies were handed, nearest the Town Center first; they change hands before
the Allies' buildings drop to 1 HP (run_xs waits for it).

Starting soldiers stand in slots by the Wonder, placed by hand (2026-11-17): Clubmen fill the first three melee slots,
Axemen take their place and add two; Bowmen fill the ranged slots, the Scout its own.

Other upgrades unlock techs locked by run_rules (unlocks()), or hand the player the base's walls (still damaged:
run_xs rolls them after).
"""

from math import dist

from aoe2ed import blocks

from crucible import meta

VILLAGER_MALE, VILLAGER_FEMALE = 83, 293
HOUSE, CLUBMAN, AXEMAN, BOWMAN, SCOUT = 70, 281, 531, 4, 448
WALLS = (72, 117, 155)  # Small, Medium, Fortified Wall
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
KEPT = {  # upgrade -> (the building type each level keeps, how many of that type nearer the Town Center to skip)
    meta.HOUSES.key: (HOUSE, 0),
    meta.GRANARY_UPGRADE.key: (meta.GRANARY, 0),
    meta.STORAGE_PIT_UPGRADE.key: (meta.STORAGE_PIT, 0),
    meta.BARRACKS_UPGRADE.key: (meta.BARRACKS, 0),
    meta.SECOND_BARRACKS.key: (meta.BARRACKS, 1),
    meta.MARKET_UPGRADE.key: (meta.MARKET, 0),
    meta.ARCHERY_RANGE_UPGRADE.key: (meta.ARCHERY_RANGE, 0),
    meta.STABLE_UPGRADE.key: (meta.STABLE, 0),
}
BRONZE_AGE, AXE, WATCH_TOWER = 102, 63, 16  # techs
STORAGE_PIT_ROW = (46, 40, 41, 42)  # its Tool Age techs: Tool Working, Leather Armor for soldiers, archers, cavalry


def unlocks(market_techs: list[int]) -> dict[str, tuple[int, ...]]:
    """Upgrade -> the techs it unlocks. `market_techs`: run_rules.techs_at(data, meta.MARKET)."""
    return {
        meta.BRONZE_AGE.key: (BRONZE_AGE,),
        meta.AXE.key: (AXE,),
        meta.MARKET_TECHS.key: tuple(market_techs),
        meta.STORAGE_PIT_TECHS.key: STORAGE_PIT_ROW,
        meta.TOWER.key: (WATCH_TOWER,),
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
    (AoE's rule), so a working one (Barracks, Granary, Storage Pit) is removed and, a second later, created anew for the
    player on its tile, to age up like one the player built. Nothing else may stand on that tile: a building isn't
    created over anything (a berry bush under the arena's Granary kept it from coming back, so the bush is gone). (Replacing it with the next age's unit lost its buttons: units train at the Age1
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
    unlocked: dict[str, tuple[int, ...]],
) -> None:
    """`villagers`: where each extra villager starts (tile centres), in order. `chains`: age_chains(). `unlocked`:
    unlocks()."""
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

    for key, (building, skip) in KEPT.items():
        upgrade = next(u for u in meta.UPGRADES if u.key == key)
        candidates = sorted(
            (u for u in s.unit_manager.units[allies] if u.unit_const == building),
            key=lambda u: dist((u.x, u.y), town_center),
        )[skip : skip + upgrade.levels]
        if building in LOOKS_ONLY:
            kept += candidates

        for level, unit in enumerate(candidates, start=1):
            _keep(ctx, f"Meta: {upgrade.title} {level}", _at_least(key, level), unit, allies, player)

    _ages(ctx, kept, chains, player)
    _soldiers(ctx, player)

    for key, techs in unlocked.items():
        upgrade = next(u for u in meta.UPGRADES if u.key == key)
        ctx.trigger(
            f"Meta: {upgrade.title} unlocked",
            _at_least(key, 1),
            [
                {"type": "enable_disable_technology", "source_player": player, "technology": tech, "enabled": 1}
                for tech in techs
            ],
        )

    walls = [
        {"type": "change_ownership", "source_player": allies, "target_player": player, "object_list_unit_id": wall}
        for wall in WALLS
    ]
    ctx.trigger("Meta: walls", _at_least(meta.WALLS.key, 1), walls)


def _create(unit: int, player: int, tiles) -> list[dict]:
    return [
        {"type": "create_object", "object_list_unit_id": unit, "source_player": player, "location": list(tile)}
        for tile in tiles
    ]


def _soldiers(ctx, player: int) -> None:
    """Clubmen in the first three melee slots, unless they're Axemen; the second Axemen level fills the other two.
    Bowmen: 3, then one more per level; the Scout."""
    melee, ranged = SLOTS["melee"], SLOTS["ranged"]
    no_axemen = [{"type": "variable_value", "variable": meta.AXEMEN.key, "comparison": "LESS", "quantity": 1}]
    ctx.trigger(
        "Meta: Clubmen",
        _at_least(meta.CLUBMEN.key, 1) + no_axemen,
        _create(CLUBMAN, player, melee[: meta.CLUBMEN_PER_LEVEL]),
    )
    done = 0

    for level, amount in enumerate(meta.AXEMEN.amounts, start=1):
        tiles, done = melee[done : done + amount], done + amount
        ctx.trigger(f"Meta: Axemen {level}", _at_least(meta.AXEMEN.key, level), _create(AXEMAN, player, tiles))

    done = 0

    for level, amount in enumerate(meta.BOWMEN.amounts, start=1):
        tiles, done = ranged[done : done + amount], done + amount
        ctx.trigger(f"Meta: Bowmen {level}", _at_least(meta.BOWMEN.key, level), _create(BOWMAN, player, tiles))

    ctx.trigger("Meta: Scout", _at_least(meta.SCOUT.key, 1), _create(SCOUT, player, SLOTS["scout"]))
