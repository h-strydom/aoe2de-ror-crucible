"""crucible_hub: the camp between runs, built from the hand-made map (assets/meta).

Player 1 is the player: the Town Center and the Wonder, with only the hub's own buttons (meta.py). Player 2 looks
like the player (purple) but isn't: it holds what the next run will start with. Players 3 (tier 1) and 4 (tier 2, in
the Tool Age) are gray: what can still be bought.

Upgrades are researched at places (meta.PLACES). A place is the player's, marked "(!)", while it has an upgrade on
offer; once it has none it turns purple (player 2) and loses the mark. An upgrade is on offer while its tier is open
(meta.TIERS: so many bought from the tier before), its place is bought, what it requires is bought and it has levels
left. Each place lists its upgrades on offer with a count line ("4/10 villagers"), each line the caption of a flag
below it; the Wonder's first line counts towards the next tier ("0/5 until Tier 2").

An XS rule works out what's on offer every second and signals each change through a trigger variable; looping
triggers act on it (Enable/Disable Technology, Change Ownership, Change Object Caption: XS can do none of them).

Workers look busy but gather nothing: purple villagers on the berries, gray ones on the stone and gold, all at work
rate 0.

Upgrades are kept in the campaign bank (only inside the Crucible campaign; a standalone hub forgets them). The hub
loads them at the start, so a return shows everything already bought. "Begin the Crucible" ends the hub in a victory,
which starts the run. A decision at the start can reset every upgrade (it takes effect on the next start).
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
from crucible.scenarios import datamod_check
from crucible.scenarios.maps import asset

NAME = "crucible_hub"
GAIA, PLAYER, PURPLE, GRAY, GRAY_2 = 0, 1, 2, 3, 4
OWNERS = {"player": PLAYER, "gray": GRAY, "tier2": GRAY_2}  # a place's owner in the map
WONDER, HOUSE, CLUBMAN, AXEMAN, BOWMAN, SCOUT = 276, 70, 281, 531, 4, 448
VILLAGERS = (83, 293)
VILLAGER_JOBS = (83, 293, 120, 354, 579, 581, 124, 220)  # base, forager, gold and stone miner (male, female)
BERRIES, GOLD_MINE, STONE_MINE = 59, 66, 102
RESOURCES = (BERRIES, GOLD_MINE, STONE_MINE)
WORK_RATE = 13
BERRY_REACH = 3  # villagers this close to a berry bush start purple
REVEAL_MAP = 203  # resource: 2 = the whole map visible, no fog
GARRISON_CAPACITY = 2
FLAG = 600  # Flag A: carries a count line's caption
LINE_STEP = 0.5  # tiles between count lines, down the screen (a step in x and y)
MARK = "(!)"
RESET_VARIABLE = "hub_reset"
TIER_VARIABLE = "hub_tier"


def _units(s, player: int, types) -> list:
    return [u for u in s.unit_manager.units[player] if u.unit_const in types]


def _by_id(units) -> list:
    return sorted(units, key=lambda u: u.reference_id)


def _nearest(unit, others):
    return min(others, key=lambda o: dist((unit.x, unit.y), (o.x, o.y)))


def _on(variable: str, value: int, name: str, effects: list[dict]) -> dict:
    """Looping: act when XS sets `variable` to `value`, then clear it for the next signal."""
    return {
        "name": name,
        "conditions": [{"type": "variable_value", "variable": variable, "comparison": "EQUAL", "quantity": value}],
        "effects": [*effects, {"type": "change_variable", "variable": variable, "operation": "SET", "quantity": 0}],
        "looping": True,
    }


def _variable_id(ctx, name: str) -> int:
    ctx.var(name)

    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def _state_variable(upgrade: meta.Upgrade) -> str:
    return f"{upgrade.key}_state"


def _place_variable(place: meta.Place) -> str:
    return f"hub_place_{place.key}"


def _default_buttons() -> tuple[list[int], list[int]]:
    """What RoR's buildings at the hub's places train or research: none of it in the hub."""
    data = source_dat()
    places = {p.unit for p in meta.PLACES}
    units = [
        i
        for i, u in enumerate(data.civs[Style.GREEK].units)
        if u and u.creatable and any(c.unit_id in places for c in u.creatable.train_locations)
    ]
    techs = [i for i, t in enumerate(data.techs) if any(r.location_id in places for r in t.research_locations)]

    return units, techs


def _places(s) -> dict[str, object]:
    """Each place's building in the map."""
    return {p.key: _units(s, OWNERS[p.owner], (p.unit,))[0] for p in meta.PLACES}


def _move(player: int, refs: list[int], to: int, orders: dict[int, list[dict]]) -> list[dict]:
    move = {"type": "change_ownership", "source_player": player, "target_player": to, "selected_object_ids": refs}

    return [move, *(order | {"source_player": to} for ref in refs for order in orders.get(ref, []))]


def _plan(s, orders: dict[int, list[dict]]) -> dict[str, list[list[dict]]]:
    """For each upgrade that shows in the hub as units changing hands: the effects of each level. Buildings bought
    are places (_place_triggers)."""
    town_center = _units(s, PLAYER, (meta.TOWN_CENTER,))[0]

    def by_distance(units):
        return sorted(units, key=lambda u: dist((u.x, u.y), (town_center.x, town_center.y)))

    def levels(units, amounts, player):
        done, found = 0, []

        for amount in amounts:
            found.append(_move(player, [u.reference_id for u in units[done : done + amount]], PURPLE, orders))
            done += amount

        return found

    villagers = _by_id(_units(s, GRAY, VILLAGERS))
    houses = by_distance(_units(s, GRAY, (HOUSE,)))
    clubmen = _units(s, GRAY, (CLUBMAN,))
    axemen = _by_id(_units(s, GRAY_2, (AXEMAN,)))
    no_clubmen = {
        "type": "remove_object",
        "source_player": PURPLE,
        "selected_object_ids": [u.reference_id for u in clubmen],
    }
    axemen_levels = levels(axemen, meta.AXEMEN.amounts, GRAY_2)
    axemen_levels[0] = [no_clubmen, *axemen_levels[0]]  # the starting Clubmen become Axemen

    return {
        meta.VILLAGERS.key: levels(villagers, (1,) * len(villagers), GRAY),
        meta.HOUSES.key: levels(houses, (1,) * len(houses), GRAY),
        meta.CLUBMEN.key: levels(clubmen, (len(clubmen),), GRAY),
        meta.AXEMEN.key: axemen_levels,
        meta.BOWMEN.key: levels(_by_id(_units(s, GRAY_2, (BOWMAN,))), meta.BOWMEN.amounts, GRAY_2),
        meta.SCOUT.key: levels(_units(s, GRAY_2, (SCOUT,)), (1,), GRAY_2),
    }


def _work(s) -> dict[int, list[dict]]:
    """Each villager's order to gather from its nearest resource, by villager."""
    resources = [u for u in s.unit_manager.units[GAIA] if u.unit_const in RESOURCES]
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
    player_set(o.handle, PURPLE, {"tribe_name": "Civilians", "color": 5, "human": False, "ai": "immobile"})

    for player in range(GRAY, s.player_manager.active_players + 1):
        player_set(o.handle, player, {"color": 6, "human": False, "ai": "immobile"})

    player_set(o.handle, GRAY_2, {"starting_age": "FEUDAL"})  # Tool Age: tier 2 looks it

    for player in range(1, s.player_manager.active_players + 1):
        others = [p for p in range(1, s.player_manager.active_players + 1) if p != player]
        diplomacy_set(o.handle, player, others, "ALLY")

    # everyone is allied, so a Conquest victory would be met at once
    options_set(o.handle, {"victory_condition": "CUSTOM", "victory_conquest": False})

    # the villagers at the berries are the run's first four: purple from the start
    bushes = [u for u in s.unit_manager.units[GAIA] if u.unit_const == BERRIES]
    near = [v for v in _units(s, GRAY, VILLAGERS) if min(dist((v.x, v.y), (b.x, b.y)) for b in bushes) <= BERRY_REACH]
    s.unit_manager.change_ownership(near, PURPLE)


def _flags(s, places: dict[str, object]) -> dict[str, list[int]]:
    """Place -> the flags carrying its count lines (the Wonder's first: the tier line), stepping down the screen from
    the building's lowest corner."""
    found = {}

    for p in meta.PLACES:
        building = places[p.key]
        lines = len([u for u in meta.UPGRADES if u.place == p.key]) + (p.unit == WONDER)
        half = 2 if p.unit == WONDER else 1.5
        found[p.key] = [
            s.unit_manager.add_unit(
                player=GAIA,
                unit_const=FLAG,
                x=building.x + half + k * LINE_STEP,
                y=building.y + half + k * LINE_STEP,
            ).reference_id
            for k in range(lines)
        ]

    return found


def _caption(refs: list[int], text: str) -> dict:
    return {"type": "change_object_caption", "source_player": GAIA, "selected_object_ids": refs, "message": text}


def _tile(unit) -> list[int]:
    return [int(unit.x), int(unit.y), int(unit.x), int(unit.y)]


def _start(ctx, techs: dict[str, int], orders: dict[int, list[dict]], places: dict[str, object]) -> None:
    units, default_techs = _default_buttons()
    hub_techs = [techs[u.tech] for u in meta.UPGRADES]  # each on once XS says it's on offer
    off = [
        *(
            {"type": "enable_disable_object", "source_player": PLAYER, "object_list_unit_id": u, "enabled": 0}
            for u in units
        ),
        *(
            {"type": "enable_disable_technology", "source_player": PLAYER, "technology": t, "enabled": 0}
            for t in [*default_techs, *hub_techs, techs[SEND_WAVE], techs[choice_key(1)], techs[choice_key(2)]]
        ),
    ]
    town_centers = (meta.TOWN_CENTER, techs[meta.place("town_center_2").copy_key])
    no_bell = [  # nothing can garrison, so no town bell (or ungarrison) button
        {
            "type": "modify_attribute",
            "source_player": PLAYER,
            "object_list_unit_id": unit,
            "object_attributes": GARRISON_CAPACITY,
            "operation": "SET",
            "quantity": 0,
        }
        for unit in town_centers
    ]
    ctx.trigger("Hub: only the hub's buttons", [], [*off, *no_bell])
    copies = [
        {
            "type": "replace_object",
            "source_player": GRAY_2,
            "target_player": GRAY_2,
            "object_list_unit_id": p.unit,
            "object_list_unit_id_2": techs[p.copy_key],
            "area": _tile(places[p.key]),
        }
        for p in meta.PLACES
        if p.copy_of >= 0
    ]
    ctx.trigger("Hub: tier 2 Town Center and Barracks are the hub's copies", [], copies)
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
    reveal = {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": PLAYER, "quantity": 2}
    ctx.trigger("Hub: whole map revealed", [], [reveal | {"operation": "SET"}])
    ctx.trigger("Hub: workers look busy", [], [*idle, *(e for order in orders.values() for e in order)])
    blocks.bank.load(ctx, {upgrade.key: 0 for upgrade in meta.UPGRADES}, name="Hub: load upgrades")


def _upgrade(ctx, upgrade: meta.Upgrade, tech: int, levels: list[list[dict]], line: int) -> None:
    """`levels`: the effects of each level (_plan). `line`: the flag of its count line."""
    key, state = upgrade.key, _state_variable(upgrade)
    enable = {"type": "enable_disable_technology", "source_player": PLAYER, "technology": tech}
    most = upgrade.count(upgrade.levels)
    ctx.var(state)
    ctx.triggers(
        {
            "name": f"Hub: {upgrade.title} bought",
            "conditions": [{"type": "research_technology", "source_player": PLAYER, "technology": tech}],
            "effects": [
                {"type": "change_variable", "variable": key, "operation": "ADD", "quantity": 1},
                {"type": "store_key_value", "variable": key, "message": key},
            ],
            "looping": True,
        },
        _on(state, 1, f"Hub: {upgrade.title} not on offer", [enable | {"enabled": 0}, _caption([line], "")]),
        *(
            _on(
                state,
                level + 2,
                f"Hub: {upgrade.title} on offer at {level}",
                [
                    enable | {"enabled": 1},  # a research takes the button away: this brings it back for the next
                    _caption([line], f"{upgrade.count(level)}/{most} {upgrade.label}"),
                ],
            )
            for level in range(upgrade.levels)
        ),
    )

    for level, effects in enumerate(levels, start=1):
        ctx.trigger(
            f"Hub: {upgrade.title} {level}",
            [{"type": "variable_value", "variable": key, "comparison": "LARGER_OR_EQUAL", "quantity": level}],
            effects,
        )


def _place_triggers(ctx, place: meta.Place, building, techs: dict[str, int]) -> None:
    """XS sets the place's variable to 1: on offer (the player's, marked), 2: nothing on offer (purple, unmarked)."""
    variable = _place_variable(place)
    ctx.var(variable)
    where = {"object_list_unit_id": meta.location(place, techs), "area": _tile(building)}
    mark = {"type": "change_object_caption", "source_player": PLAYER, **where}

    if place.owner == "player":  # always the player's: the Begin button is on the Town Center
        on, off = [mark | {"message": MARK}], [mark | {"message": ""}]
    else:
        moves = {
            to: [
                {"type": "change_ownership", "source_player": owner, "target_player": to, **where}
                for owner in (PLAYER, PURPLE, OWNERS[place.owner])
                if owner != to
            ]
            for to in (PLAYER, PURPLE)
        }
        on, off = [*moves[PLAYER], mark | {"message": MARK}], [mark | {"message": ""}, *moves[PURPLE]]

    ctx.triggers(
        _on(variable, 1, f"Hub: {place.key} on offer", on),
        _on(variable, 2, f"Hub: {place.key} nothing on offer", off),
    )


def _tier_lines() -> list[str]:
    """The Wonder's tier line by state: so many of TIERS[0] bought from tier 1, then of TIERS[1] from tier 2, then
    nothing."""
    lines = [f"{n}/{meta.TIERS[0]} until Tier 2" for n in range(meta.TIERS[0])]
    lines += [f"{n}/{meta.TIERS[1]} until Tier 3" for n in range(meta.TIERS[1])]

    return [*lines, ""]


def _tier_triggers(ctx, line: int) -> None:
    ctx.var(TIER_VARIABLE)
    ctx.triggers(
        *(
            _on(TIER_VARIABLE, n + 1, f"Hub: tier line {n}", [_caption([line], text)])
            for n, text in enumerate(_tier_lines())
        )
    )


def _reset(ctx) -> None:
    """A decision at every start: reset every upgrade to nothing bought. The bank is cleared at once; the hub shows it
    from its next start (everything already bought stays in view until then, nothing more can be bought)."""
    ctx.var(RESET_VARIABLE)
    decision = ctx.next_decision_id()
    zero = [
        effect
        for upgrade in meta.UPGRADES
        for effect in (
            {"type": "change_variable", "variable": upgrade.key, "operation": "SET", "quantity": 0},
            {"type": "store_key_value", "variable": upgrade.key, "message": upgrade.key},
        )
    ]
    ctx.triggers(
        {
            "name": "Hub: reset progress?",
            "conditions": [],
            "effects": [
                {
                    "type": "create_decision",
                    "decision_id": decision,
                    "message": "Reset all your progress? Every upgrade bought is lost.",
                    "message_option1": "Reset everything",
                    "message_option2": "Keep my progress",
                }
            ],
        },
        {
            "name": "Hub: reset progress",
            "conditions": [{"type": "decision_triggered", "decision_id": decision, "decision_option": 1}],
            "effects": [
                {"type": "change_variable", "variable": RESET_VARIABLE, "operation": "SET", "quantity": 1},
                *zero,
                {
                    "type": "send_chat",
                    "source_player": PLAYER,
                    "message": "Progress reset. Restart the mission (menu, Restart) to start over.",
                },
            ],
        },
    )


XS_HELPERS = """// ---- crucible hub: what's on offer ----
int crucibleHubLast = -1;  // per upgrade, then per place, then the tier line: the last value sent

// Signal `value` (as value + 1: 0 means nothing new) when it isn't what was last sent.
void crucibleHubSend(int index = 0, int variable = -1, int value = 0) {
    if (xsArrayGetInt(crucibleHubLast, index) != value) {
        xsArraySetInt(crucibleHubLast, index, value);
        xsSetTriggerVariable(variable, value + 1);
    }
}

// An upgrade: 0 not on offer, else its level + 1.
int crucibleHubState(bool offered = false, int level = 0) {
    if (offered) {
        return (level + 1);
    }
    return (0);
}

// A place: 0 something on offer, 1 nothing.
int crucibleHubPlace(bool offered = false) {
    if (offered) {
        return (0);
    }
    return (1);
}
"""


def xs(ctx) -> str:
    """The rule that works out what's on offer (module docstring)."""
    upgrades, places = meta.UPGRADES, meta.PLACES
    level = {u.key: f"l{n}" for n, u in enumerate(upgrades)}
    first, second = meta.TIERS
    lines = [
        XS_HELPERS,
        "// The tier line: so many bought towards tier 2, then towards tier 3, then none.",
        "int crucibleHubTier(int tier1 = 0, int tier2 = 0) {",
        f"    if (tier1 < {first}) {{",
        "        return (tier1);",
        "    }",
        f"    if (tier2 < {second}) {{",
        f"        return ({first} + tier2);",
        "    }",
        f"    return ({first + second});",
        "}",
        "",
        "rule crucibleHubInit",
        "    active",
        "    highFrequency",
        "{",
        f'    crucibleHubLast = xsArrayCreateInt({len(upgrades) + len(places) + 1}, -1, "crucible hub last");',
        "    xsDisableSelf();",
        "}",
        "",
        "rule crucibleHub",
        "    active",
        "    minInterval 1",
        "{",
        "    if (xsGetTime() < 1) {",
        "        return;  // the bank's load comes first",
        "    }",
        "",
        f"    bool open = (xsTriggerVariable({_variable_id(ctx, RESET_VARIABLE)}) == 0);  // not reset",
    ]
    lines += [f"    int {level[u.key]} = xsTriggerVariable({_variable_id(ctx, u.key)});" for u in upgrades]

    for tier in (1, 2):
        lines.append(f"    int tier{tier} = {' + '.join(level[u.key] for u in upgrades if u.tier == tier)};")

    lines.append(f"    bool tier2open = (tier1 >= {first});")

    def place_open(p: meta.Place) -> str:
        if p.opened_by:
            return f"({level[p.opened_by]} >= 1)"

        return "tier2open" if p.owner == "tier2" else "true"

    for n, u in enumerate(upgrades):
        parts = [
            "open",
            f"({level[u.key]} < {u.levels})",
            place_open(meta.place(u.place)),
            *(["tier2open"] if u.tier == 2 else []),
            *(f"({level[key]} >= {need})" for key, need in u.requires),
        ]
        lines.append(f"    bool o{n} = {' && '.join(parts)};")

    lines.append("")

    for n, u in enumerate(upgrades):
        variable = _variable_id(ctx, _state_variable(u))
        lines.append(f"    crucibleHubSend({n}, {variable}, crucibleHubState(o{n}, {level[u.key]}));")

    for k, p in enumerate(places):
        offered = " || ".join(f"o{n}" for n, u in enumerate(upgrades) if u.place == p.key) or "false"
        variable = _variable_id(ctx, _place_variable(p))
        send = f"crucibleHubSend({len(upgrades) + k}, {variable}, crucibleHubPlace({offered}));"
        opened = place_open(p)
        lines.append(f"    {send}" if opened == "true" else f"    if ({opened}) {{ {send} }}")

    tier = _variable_id(ctx, TIER_VARIABLE)
    lines.append(f"    crucibleHubSend({len(upgrades) + len(places)}, {tier}, crucibleHubTier(tier1, tier2));")
    lines.append("}")

    return "\n".join(lines) + "\n"


def build(out: Path, techs: dict[str, int]) -> Path:
    """`techs`: the Crucible data mod's manifest."""
    o = SESSIONS.open(asset("meta"))
    s = o.scenario

    try:
        with games.use("ror"):
            _setup(o)
            orders = _work(s)
            plan, places = _plan(s, orders), _places(s)
            flags = _flags(s, places)
            ctx = blocks.Ctx(s)
            _start(ctx, techs, orders, places)
            _reset(ctx)
            _tier_triggers(ctx, flags["wonder"][0])

            for upgrade in meta.UPGRADES:
                on_place = [u for u in meta.UPGRADES if u.place == upgrade.place]
                line = flags[upgrade.place][on_place.index(upgrade) + (upgrade.place == "wonder")]
                _upgrade(ctx, upgrade, techs[upgrade.tech], plan.get(upgrade.key, []), line)

            for place in meta.PLACES:
                _place_triggers(ctx, place, places[place.key], techs)

            ctx.trigger(
                "Hub: begin the Crucible",
                [{"type": "research_technology", "source_player": PLAYER, "technology": techs[meta.BEGIN]}],
                [{"type": "declare_victory", "source_player": PLAYER, "enabled": True}],
            )
            ctx.xs(xs(ctx))
            datamod_check.add(ctx, techs[meta.BEGIN], player=PLAYER)
            ctx.flush_xs()

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
