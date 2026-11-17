"""crucible_hub: the camp between runs, built from the hand-made map (assets/meta).

Player 1 is the player: the Town Center and the Wonder, with only the hub's own buttons (meta.py). Player 2 looks
like the player (purple) but isn't: it holds what the next run will start with. Everyone else is gray: what can still
be bought. Each upgrade bought turns one more gray thing purple; the Barracks goes to the player, so the Clubmen can
be bought on it, then to player 2.

Workers look busy but gather nothing: purple villagers on the berries, gray ones on the stone and gold, all at work
rate 0.

Upgrades are kept in the campaign bank (only inside the Crucible campaign; a standalone hub forgets them). The hub
loads them at the start, so a return shows everything already bought. "Begin the Crucible" ends the hub in a victory,
which starts the run.
"""

from math import dist
from pathlib import Path

from aoe2ed import blocks, games
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from crucible import meta
from crucible.datamod.civs import SCENARIO_CIVS, Style
from crucible.datamod.mod import source_dat
from crucible.datamod.shop import SEND_WAVE, choice_key
from crucible.scenarios.maps import asset

NAME = "crucible_hub"
PLAYER, PURPLE, GRAY = 1, 2, 3
WONDER, GRANARY, STORAGE_PIT, HOUSE, CLUBMAN = 276, 68, 562, 70, 281
VILLAGERS = (83, 293)
VILLAGER_JOBS = (83, 293, 120, 354, 579, 581, 124, 220)  # base, forager, gold and stone miner (male, female)
BERRIES, GOLD_MINE, STONE_MINE = 59, 66, 102
RESOURCES = (BERRIES, GOLD_MINE, STONE_MINE)
WORK_RATE = 13
BERRY_REACH = 3  # villagers this close to a berry bush start purple
REVEAL_MAP = 203  # resource: 2 = the whole map visible, no fog


def _units(s, player: int, types) -> list:
    return [u for u in s.unit_manager.units[player] if u.unit_const in types]


def _nearest(unit, others):
    return min(others, key=lambda o: dist((unit.x, unit.y), (o.x, o.y)))


def _default_buttons() -> tuple[list[int], list[int]]:
    """What RoR's Town Center and Barracks train or research: none of it in the hub."""
    data = source_dat()
    places = (meta.TOWN_CENTER, meta.BARRACKS)
    units = [
        i
        for i, u in enumerate(data.civs[Style.GREEK].units)
        if u and u.creatable and any(c.unit_id in places for c in u.creatable.train_locations)
    ]
    techs = [i for i, t in enumerate(data.techs) if any(r.location_id in places for r in t.research_locations)]

    return units, techs


def _plan(s) -> dict[str, list[tuple[int, list[int], int]]]:
    """For each upgrade, per level: (from player, the objects that change hands, to player)."""
    town_center = _units(s, PLAYER, (meta.TOWN_CENTER,))[0]

    def by_distance(units):
        return sorted(units, key=lambda u: dist((u.x, u.y), (town_center.x, town_center.y)))

    villagers = sorted(_units(s, GRAY, VILLAGERS), key=lambda u: u.reference_id)
    barracks = _units(s, GRAY, (meta.BARRACKS,))[0]
    clubmen = _units(s, GRAY, (CLUBMAN,))

    return {
        meta.VILLAGERS.key: [(GRAY, [u.reference_id], PURPLE) for u in villagers],
        meta.HOUSES.key: [(GRAY, [u.reference_id], PURPLE) for u in by_distance(_units(s, GRAY, (HOUSE,)))],
        meta.GRANARY.key: [(GRAY, [u.reference_id for u in _units(s, GRAY, (GRANARY,))], PURPLE)],
        meta.STORAGE_PIT.key: [(GRAY, [u.reference_id for u in _units(s, GRAY, (STORAGE_PIT,))], PURPLE)],
        meta.BARRACKS_UPGRADE.key: [(GRAY, [barracks.reference_id], PLAYER)],
        meta.CLUBMEN.key: [
            (PLAYER, [barracks.reference_id], PURPLE),
            (GRAY, [u.reference_id for u in clubmen], PURPLE),
        ],
    }


def _work(s) -> dict[int, list[dict]]:
    """Each villager's order to gather from its nearest resource, by villager."""
    resources = [u for u in s.unit_manager.units[0] if u.unit_const in RESOURCES]
    orders = {}

    for player in (PURPLE, GRAY):
        for villager in _units(s, player, VILLAGERS):
            orders[villager.reference_id] = [
                {
                    "type": "task_object",
                    "source_player": player,
                    "selected_object_ids": [villager.reference_id],
                    "location_object_reference": _nearest(villager, resources).reference_id,
                }
            ]

    return orders


def _setup(o) -> None:
    s = o.scenario
    # only players who own something: an active player with no units is given a starting town (a Town Center and
    # villagers) and plays it
    s.player_manager.active_players = max(p for p in range(1, 9) if s.unit_manager.units[p])
    player_set(o.handle, PLAYER, {"civilization": SCENARIO_CIVS[Style.GREEK], "color": 5, "human": True})
    player_set(o.handle, PURPLE, {"color": 5, "human": False, "ai": "immobile"})

    for player in range(GRAY, s.player_manager.active_players + 1):
        player_set(o.handle, player, {"human": False, "ai": "immobile"})

    for player in range(1, s.player_manager.active_players + 1):
        others = [p for p in range(1, s.player_manager.active_players + 1) if p != player]
        diplomacy_set(o.handle, player, others, "ALLY")

    options_set(o.handle, {"victory_condition": "CUSTOM"})

    # the villagers at the berries are the run's first four: purple from the start
    bushes = [u for u in s.unit_manager.units[0] if u.unit_const == BERRIES]
    near = [v for v in _units(s, GRAY, VILLAGERS) if min(dist((v.x, v.y), (b.x, b.y)) for b in bushes) <= BERRY_REACH]
    s.unit_manager.change_ownership(near, PURPLE)


def _start(ctx, techs: dict[str, int], orders: dict[int, list[dict]]) -> None:
    units, default_techs = _default_buttons()
    off = [
        *(
            {"type": "enable_disable_object", "source_player": PLAYER, "object_list_unit_id": u, "enabled": 0}
            for u in units
        ),
        *(
            {"type": "enable_disable_technology", "source_player": PLAYER, "technology": t, "enabled": 0}
            for t in [*default_techs, techs[SEND_WAVE], techs[choice_key(1)], techs[choice_key(2)]]
        ),
    ]
    idle = [
        {
            "type": "modify_attribute",
            "source_player": player,
            "object_list_unit_id": unit,
            "object_attributes": WORK_RATE,
            "operation": "SET",
            "quantity": 0,
        }
        for player in (PURPLE, GRAY)
        for unit in VILLAGER_JOBS
    ]
    ctx.trigger("Hub: only the hub's buttons", [], off)
    reveal = {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": PLAYER, "quantity": 2}
    ctx.trigger("Hub: whole map revealed", [], [reveal | {"operation": "SET"}])
    ctx.trigger("Hub: workers look busy", [], [*idle, *(e for order in orders.values() for e in order)])
    blocks.bank.load(ctx, {upgrade.key: 0 for upgrade in meta.UPGRADES}, name="Hub: load upgrades")


def _upgrade(ctx, upgrade: meta.Upgrade, tech: int, levels, orders: dict[int, list[dict]]) -> None:
    key = upgrade.key
    enable = {"type": "enable_disable_technology", "source_player": PLAYER, "technology": tech}
    ctx.triggers(
        {
            "name": f"Hub: {upgrade.title} bought",
            "conditions": [{"type": "research_technology", "source_player": PLAYER, "technology": tech}],
            "effects": [
                {"type": "change_variable", "variable": key, "operation": "ADD", "quantity": 1},
                {"type": "store_key_value", "variable": key, "message": key},
                enable | {"enabled": 1},  # bought again next time (switched off below once at its last level)
            ],
            "looping": True,
        },
        {
            "name": f"Hub: {upgrade.title} sold out",
            "conditions": [
                {"type": "variable_value", "variable": key, "comparison": "LARGER_OR_EQUAL", "quantity": upgrade.levels}
            ],
            "effects": [enable | {"enabled": 0}],
            "looping": True,
        },
    )

    for level, (before, refs, after) in enumerate(levels, start=1):
        move = {
            "type": "change_ownership",
            "source_player": before,
            "target_player": after,
            "selected_object_ids": refs,
        }
        retask = [
            order | {"source_player": after}
            for ref in refs
            for order in orders.get(ref, [])
        ]
        level_needed = min(level, upgrade.levels)
        ctx.trigger(
            f"Hub: {upgrade.title} {level}",
            [{"type": "variable_value", "variable": key, "comparison": "LARGER_OR_EQUAL", "quantity": level_needed}],
            [move, *retask],
        )


def build(out: Path, techs: dict[str, int]) -> Path:
    """`techs`: the Crucible data mod's manifest."""
    o = SESSIONS.open(asset("meta"))
    s = o.scenario

    try:
        with games.use("ror"):
            _setup(o)
            plan, orders = _plan(s), _work(s)
            ctx = blocks.Ctx(s)
            _start(ctx, techs, orders)

            for upgrade in meta.UPGRADES:
                _upgrade(ctx, upgrade, techs[upgrade.tech], plan[upgrade.key], orders)

            ctx.trigger(
                "Hub: begin the Crucible",
                [{"type": "research_technology", "source_player": PLAYER, "technology": techs[meta.BEGIN]}],
                [{"type": "declare_victory", "source_player": PLAYER, "enabled": True}],
            )

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
