"""The meta upgrades in crucible_run: loaded from the campaign bank at the start, each level giving the player one
more of something (meta.py). Outside the Crucible campaign nothing is loaded, so a standalone run gets none.

Buildings kept come from the base the Allies were handed, nearest the Town Center first; they change hands before
the Allies' buildings drop to 1 HP (run_xs waits for it).
"""

from math import dist

from aoe2ed import blocks

from crucible import meta

VILLAGER_MALE, VILLAGER_FEMALE = 83, 293
HOUSE, GRANARY, STORAGE_PIT, CLUBMAN = 70, 68, 562, 281
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

    kept_barracks = None

    for key, building in KEPT.items():
        upgrade = next(u for u in meta.UPGRADES if u.key == key)
        candidates = sorted(
            (u for u in s.unit_manager.units[allies] if u.unit_const == building),
            key=lambda u: dist((u.x, u.y), town_center),
        )

        if building == meta.BARRACKS and candidates:
            kept_barracks = candidates[0]

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

    if kept_barracks:
        spawn = blocks.spawn(
            ctx,
            unit=CLUBMAN,
            count=meta.CLUBMEN_PER_LEVEL,
            player=player,
            at=(int(kept_barracks.x), int(kept_barracks.y) + 3),
        )
        ctx.trigger("Meta: Clubmen", _at_least(meta.CLUBMEN.key, 1), spawn)
