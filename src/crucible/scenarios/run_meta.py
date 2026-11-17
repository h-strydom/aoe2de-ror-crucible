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


def add(ctx, s, *, player: int, allies: int, town_center: tuple[float, float], villagers) -> None:
    """`villagers`: where each extra villager starts (tile centres), in order."""
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

    for key, building in KEPT.items():
        upgrade = next(u for u in meta.UPGRADES if u.key == key)
        candidates = sorted(
            (u for u in s.unit_manager.units[allies] if u.unit_const == building),
            key=lambda u: dist((u.x, u.y), town_center),
        )

        for level, unit in enumerate(candidates[: upgrade.levels], start=1):
            ctx.trigger(
                f"Meta: {upgrade.title} {level}",
                _at_least(key, level),
                [
                    {
                        "type": "change_ownership",
                        "source_player": allies,
                        "target_player": player,
                        "selected_object_ids": [unit.reference_id],
                    }
                ],
            )

    clubmen = [
        {"type": "create_object", "object_list_unit_id": CLUBMAN, "source_player": player, "location": list(tile)}
        for tile in SLOTS["melee"][: meta.CLUBMEN_PER_LEVEL]
    ]
    ctx.trigger("Meta: Clubmen", _at_least(meta.CLUBMEN.key, 1), clubmen)
