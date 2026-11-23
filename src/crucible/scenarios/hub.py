"""crucible_hub: the camp between runs (docs/meta-v2.md), built from the hand-made map (assets/metaprogression).

Player 1 is the player: the Wonder (global upgrades) and, from the start, tier 1's Town Center, 4 villagers and 2
houses. Players 2 to 6 hold the tiers (meta.TIER_PLAYERS): what can still be bought. The player's food, wood, gold and
stone are the currency the runs earn (the campaign bank's meta_food...): an upgrade's price is its tech's cost
(placeholders, free for now), and what's left is banked after every purchase.

Upgrades are researched at places (meta.PLACES): each a tier player's building, replaced in the map by the data mod's
copy of it (aged to its tier) so it shows only its own buttons. A place becomes the player's once open (its tier, and
the upgrade that buys it if any) and is captioned "(*)" while it has an upgrade on offer, "(!)" while one is
affordable. An upgrade is on offer while its tier is open (meta.TIERS: so many more levels bought, from any tier), its
place is open, what it requires is bought and it has levels left (the Wonder's grow with the tiers: `caps`). Its button
counts its levels: the icon shows "2/6" (the data mod's count icons) and the name "Villager (2/6)" (renamed by XS).
Buying a level can hand over units of the place's player (`shows`: the villagers, Clubmen... the run starts with).

An objective counts towards the next tier ("0/5 upgrades until Tier 2"); reaching it hands over that tier's buildings
(meta.TIER_GIVEN) and may give a reward (the Bronze Age at tier 3, the Iron Age at 4: researchable in the run).
Objective text can't show a variable but can show a player's relics (`<Relics Captured, 2>`), so XS keeps each
tier's count in its own player's relics (TIER_COUNTERS), capped at what the tier needs.

An XS rule works out what's on offer every second and signals each change through a trigger variable; looping triggers
act on it (Enable/Disable Technology, Change Ownership, Change Object Caption: XS can do none of them).

Each tier player keeps a Barracks in the map's north corner (KEEPERS): once everything is bought their buildings
and units are all the player's, and a player with nothing left is defeated; with every other player gone the hub
was won at once (playtest 2026-11-23). A house isn't enough: it has to be a building that produces.

Upgrades and the currency are kept in the campaign bank (only inside the Crucible campaign; a standalone hub forgets
them). A decision at the start, left open while the player shops, either resets every upgrade (refunding what they
cost) or saves; either way it wins, and the victory starts the run.
"""

from math import dist
from pathlib import Path

from aoe2ed import blocks, games
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from crucible import meta
from crucible.datamod import count_icons
from crucible.datamod.civs import SCENARIO_CIVS, Style
from crucible.datamod.mod import source_dat
from crucible.datamod.shop import SEND_WAVE, choice_key
from crucible.scenarios import datamod_check
from crucible.scenarios.maps import asset

NAME = "crucible_hub"
GAIA, PLAYER = 0, 1
WONDER, HOUSE = meta.WONDER, meta.HOUSE
VILLAGERS = meta.VILLAGER_TYPES
REVEAL_MAP = 203  # resource: 2 = the whole map visible, no fog
GARRISON_CAPACITY = 2
ON_OFFER, AFFORDABLE = "(*)", "(!)"
NO_CAPTION = " "  # an empty caption left the old "(!)" up (playtest 2026-11-22)
RESET_VARIABLE = "hub_reset"  # 1: refund (XS), 2: clear the upgrades (triggers)
RELICS = 7  # the resource objective text knows as "Relics Captured"
TIER_COUNTERS = (2, 3, 4, 5)  # whose relics count towards tier 2, 3, 4, 5: nothing else uses them
STOCKPILE = ("FOOD_STORAGE", "WOOD_STORAGE", "GOLD_STORAGE", "STONE_STORAGE")  # meta.CURRENCY, in order
XS_RESOURCES = ("cAttributeFood", "cAttributeWood", "cAttributeGold", "cAttributeStone")
AGES = {1: "DARK", 2: "FEUDAL", 3: "CASTLE", 4: "IMPERIAL", 5: "IMPERIAL"}  # tier -> its player's age (its looks)
SHOP_TECHS = (SEND_WAVE, choice_key(1), choice_key(2))  # the run's buttons on the Wonder: off in the hub
KEEPER = meta.BARRACKS  # not a type anything hands over by type once the plan is made
KEEPERS = tuple((2.5 + 4 * n, 2.5) for n in range(len(meta.TIER_PLAYERS)))  # each tier player's, in turn


def _units(s, player: int, types) -> list:
    return [u for u in s.unit_manager.units[player] if u.unit_const in types]


def _by_distance(units, to) -> list:
    return sorted(units, key=lambda u: (dist((u.x, u.y), (to.x, to.y)), u.reference_id))


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


def _move(player: int, refs: list[int], to: int = PLAYER) -> dict:
    return {"type": "change_ownership", "source_player": player, "target_player": to, "selected_object_ids": refs}


def _hand_over(player: int, unit, to: int = PLAYER) -> dict:
    """One unit to the player, by its type and tile (not its reference id: units bought by id were left behind in
    play, playtest 2026-11-22)."""
    x, y = int(unit.x), int(unit.y)

    return {
        "type": "change_ownership",
        "source_player": player,
        "target_player": to,
        "object_list_unit_id": unit.unit_const,
        "area": [x, y, x, y],
    }


def _setup(o, techs: dict[str, int]) -> dict[str, object]:
    """The players, and each place's building replaced by its copy; returns each place's building."""
    s = o.scenario
    players = (PLAYER, *meta.TIER_PLAYERS.values())
    s.player_manager.active_players = max(players)
    player_set(
        o.handle,
        PLAYER,
        {"civilization": SCENARIO_CIVS[Style.GREEK], "color": 5, "human": True}
        | {"food": 0, "wood": 0, "gold": 0, "stone": 0},
    )

    for tier, player in meta.TIER_PLAYERS.items():
        player_set(o.handle, player, {"human": False, "ai": "immobile", "starting_age": AGES[tier]})

    for player in players:
        diplomacy_set(o.handle, player, [p for p in players if p != player], "ALLY")

    # everyone is allied, so a Conquest victory would be met at once
    options_set(o.handle, {"victory_condition": "CUSTOM", "victory_conquest": False})

    buildings = {}

    for place in meta.PLACES:
        building = _units(s, place.player, (place.unit,))[0]

        if place.copy:
            building.unit_const = techs[place.copy_key]

        buildings[place.key] = building

    # the player's from the start: tier 1's Town Center, 4 villagers, 2 houses (nearest the Town Center)
    town_center = buildings["town_center_1"]
    start = [town_center]
    start += _by_distance(_units(s, meta.TIER_PLAYERS[1], VILLAGERS), town_center)[: meta.START_VILLAGERS]
    start += _by_distance(_units(s, meta.TIER_PLAYERS[1], (HOUSE,)), town_center)[: meta.START_GIVEN[HOUSE]]
    s.unit_manager.change_ownership(start, PLAYER)

    return buildings


def _plan(s, buildings: dict[str, object]) -> dict[str, list[list[dict]]]:
    """Each upgrade's effects by level: its place's player's units of `shows` handed over (nearest the place first),
    each unit to one upgrade only (the Axemen upgrade's three, then the Axemen's two)."""
    plans = {}
    clubmen = []
    taken = set()

    for upgrade in meta.UPGRADES:
        if not upgrade.shows:
            continue

        place = meta.place(upgrade.place)
        found = _units(s, place.player, upgrade.shows)
        units = [u for u in _by_distance(found, buildings[place.key]) if u.reference_id not in taken]
        per = upgrade.per or ((1,) * upgrade.levels if upgrade.levels > 1 else (len(units),))
        levels, done = [], 0

        for amount in per:
            chosen = units[done : done + amount]
            taken.update(u.reference_id for u in chosen)
            levels.append([_hand_over(place.player, u) for u in chosen])
            done += amount

        if upgrade is meta.CLUBMEN:
            clubmen = [u.reference_id for u in units]

        plans[upgrade.key] = levels

    if clubmen:  # the starting Clubmen become Axemen
        no_clubmen = {"type": "remove_object", "source_player": PLAYER, "selected_object_ids": clubmen}
        plans[meta.AXE.key][0] = [no_clubmen, *plans[meta.AXE.key][0]]

    return plans


def _start(ctx, techs: dict[str, int]) -> None:
    data = source_dat()
    trained = [
        i
        for i, u in enumerate(data.civs[Style.GREEK].units)
        if u and u.creatable and any(c.unit_id >= 0 for c in u.creatable.train_locations)
    ]
    off = [
        *(
            {"type": "enable_disable_object", "source_player": PLAYER, "object_list_unit_id": u, "enabled": 0}
            for u in trained
        ),
        *(
            {"type": "enable_disable_technology", "source_player": PLAYER, "technology": tech, "enabled": 0}
            for tech in [*(techs[u.tech] for u in meta.UPGRADES), *(techs[key] for key in SHOP_TECHS)]
        ),
    ]
    town_centers = [techs[p.copy_key] for p in meta.PLACES if p.unit == meta.TOWN_CENTER]
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
    reveal = {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": PLAYER, "quantity": 2}
    ctx.trigger("Hub: whole map revealed", [], [reveal | {"operation": "SET"}])
    blocks.bank.load(ctx, dict.fromkeys((*meta.KEYS, *meta.CURRENCY), 0), name="Hub: load upgrades")
    ctx.trigger(
        "Hub: the stockpile is the currency",
        [{"type": "timer", "timer": 1}],  # after the bank's load
        [blocks.bank.var_to_resource(key, resource) for key, resource in zip(meta.CURRENCY, STOCKPILE, strict=True)],
    )


def _bank_currency() -> list[dict]:
    """The stockpile back into the currency's variables, and into the bank."""
    return [
        effect
        for key, resource in zip(meta.CURRENCY, STOCKPILE, strict=True)
        for effect in (
            blocks.bank.resource_to_var(key, resource),
            {"type": "store_key_value", "variable": key, "message": key},
        )
    ]


def _upgrade(ctx, upgrade: meta.Upgrade, tech: int, levels: list[list[dict]], icons: dict[str, int]) -> None:
    """`levels`: the effects of each level (_plan). `icons`: the data mod's manifest (its count icons).

    Bought, the tech is switched on and off again: on resets it from researched (the bought trigger would otherwise
    fire every second until it's reset: a level bought counted twice), off keeps it hidden until XS offers the next
    level. What's left of the stockpile is banked."""
    key, state = upgrade.key, _state_variable(upgrade)
    enable = {"type": "enable_disable_technology", "source_player": PLAYER, "technology": tech}
    ctx.var(state)
    ctx.var(key)

    for currency in meta.CURRENCY:
        ctx.var(currency)

    ctx.triggers(
        {
            "name": f"Hub: {upgrade.title} bought",
            "conditions": [{"type": "research_technology", "source_player": PLAYER, "technology": tech}],
            "effects": [
                {"type": "change_variable", "variable": key, "operation": "ADD", "quantity": 1},
                {"type": "store_key_value", "variable": key, "message": key},
                *_bank_currency(),
                enable | {"enabled": 1},
                enable | {"enabled": 0},
            ],
            "looping": True,
        },
        _on(state, 1, f"Hub: {upgrade.title} not on offer", [enable | {"enabled": 0}]),
        *(
            _on(
                state,
                level + 2,
                f"Hub: {upgrade.title} on offer at {level}",
                [
                    enable | {"enabled": 1},
                    {
                        "type": "change_technology_icon",
                        "source_player": PLAYER,
                        "technology": tech,
                        "quantity": icons[count_icons.key(count_icons.label(upgrade, level))],
                    },
                ],
            )
            for level in range(upgrade.levels)
        ),
    )

    for level, effects in enumerate(levels, start=1):
        if effects:
            ctx.trigger(
                f"Hub: {upgrade.title} {level}",
                [{"type": "variable_value", "variable": key, "comparison": "LARGER_OR_EQUAL", "quantity": level}],
                effects,
            )


def _place_triggers(ctx, place: meta.Place, building) -> None:
    """XS sets the place's variable once it's open: 1 nothing on offer, 2 an upgrade on offer, 3 one affordable. Each
    also hands the place to the player (a no-op once it's theirs)."""
    variable = _place_variable(place)
    ctx.var(variable)
    ref = [building.reference_id]
    caption = {"type": "change_object_caption", "source_player": PLAYER, "selected_object_ids": ref}
    give = [] if place.player == PLAYER else [_move(place.player, ref)]

    ctx.triggers(
        *(
            _on(variable, value, f"Hub: {place.key} {label}", [*give, caption | {"message": text}])
            for value, label, text in (
                (1, "nothing on offer", NO_CAPTION),
                (2, "on offer", ON_OFFER),
                (3, "affordable", AFFORDABLE),
            )
        )
    )


def _tier_objectives(ctx, s) -> None:
    """An objective per tier after the first, each started by the one before: "0/5 upgrades until Tier 2". Reaching a
    tier hands over its buildings (meta.TIER_GIVEN) and stores its rewards."""
    names = [f"Hub: Tier {n + 2}" for n in range(len(meta.TIERS))]
    specs = []

    for n, (name, need) in enumerate(zip(names, meta.TIERS, strict=True)):
        tier = n + 2
        player = meta.TIER_PLAYERS[tier]
        rewards = [r for r in meta.REWARDS if r.tier == tier]
        given = "".join(f" ({r.title})" for r in rewards)
        more = " more" if n else ""
        text = f"<Relics Captured, {TIER_COUNTERS[n]}>/{need}{more} upgrades until Tier {tier}{given}"
        later = [{"type": "activate_trigger", "trigger_id": names[n + 1]}] if n + 1 < len(names) else []
        buildings = [u.reference_id for u in _units(s, player, meta.TIER_GIVEN[tier])]
        later += [_move(player, buildings)] if buildings else []
        later += [
            effect
            for r in rewards
            for effect in (
                {"type": "change_variable", "variable": r.key, "operation": "SET", "quantity": 1},
                {"type": "store_key_value", "variable": r.key, "message": r.key},
            )
        ]
        reached = {"type": "accumulate_attribute", "source_player": TIER_COUNTERS[n], "attribute": RELICS}
        specs.append(
            {
                "name": name,
                "conditions": [reached | {"quantity": need}],
                "effects": later,
                "enabled": n == 0,
                "display_as_objective": True,
                "display_on_screen": True,
                "description": text,
                "short_description": text,
            }
        )

    ctx.triggers(*specs)  # together: each activates the next


def _reset(ctx) -> None:
    """A decision at every start, left open while the player shops: reset every upgrade to nothing bought (refunding
    what they cost: XS adds it to the stockpile, then the triggers clear the bank) and win, or save and win (the hub
    ends and the run starts; every purchase is stored as it's made)."""
    ctx.var(RESET_VARIABLE)
    decision = ctx.next_decision_id()
    zero = [
        effect
        for key in meta.KEYS
        for effect in (
            {"type": "change_variable", "variable": key, "operation": "SET", "quantity": 0},
            {"type": "store_key_value", "variable": key, "message": key},
        )
    ]
    win = [{"type": "declare_victory", "source_player": PLAYER, "enabled": True}]
    ctx.triggers(
        {
            "name": "Hub: reset or win?",
            "conditions": [],
            "effects": [
                {
                    "type": "create_decision",
                    "decision_id": decision,
                    "message": "Reset all your upgrades (what they cost comes back), or save and start the run?",
                    "message_option1": "Reset everything",
                    "message_option2": "Save and win",
                }
            ],
        },
        {
            "name": "Hub: reset progress",
            "conditions": [{"type": "decision_triggered", "decision_id": decision, "decision_option": 1}],
            "effects": [{"type": "change_variable", "variable": RESET_VARIABLE, "operation": "SET", "quantity": 1}],
        },
        {
            "name": "Hub: reset refunded",
            "conditions": [
                {"type": "variable_value", "variable": RESET_VARIABLE, "comparison": "EQUAL", "quantity": 2}
            ],
            "effects": [*zero, *_bank_currency(), *win],  # cleared, and on to the run
        },
        {
            "name": "Hub: save and win",
            "conditions": [{"type": "decision_triggered", "decision_id": decision, "decision_option": 2}],
            "effects": win,
        },
    )


XS_HELPERS = """// ---- crucible hub: what's on offer ----
int crucibleHubLast = -1;  // per upgrade, then per place: the last value sent

// Signal `value` (as value + 1: 0 means nothing new) when it isn't what was last sent; whether it was sent.
bool crucibleHubSend(int index = 0, int variable = -1, int value = 0) {
    if (xsArrayGetInt(crucibleHubLast, index) == value) {
        return (false);
    }
    xsArraySetInt(crucibleHubLast, index, value);
    xsSetTriggerVariable(variable, value + 1);
    return (true);
}

// The same, whether sent or not.
void crucibleHubSignal(int index = 0, int variable = -1, int value = 0) {
    if (crucibleHubSend(index, variable, value)) {
        return;
    }
}

// An upgrade: 0 not on offer, else its level + 1.
int crucibleHubState(bool offered = false, int level = 0) {
    if (offered) {
        return (level + 1);
    }
    return (0);
}

// A place: 0 nothing on offer, 1 something on offer, 2 something affordable.
int crucibleHubPlace(bool offered = false, bool affordable = false) {
    if (affordable) {
        return (2);
    }
    if (offered) {
        return (1);
    }
    return (0);
}

int crucibleHubBetween(int value = 0, int least = 0, int most = 0) {
    if (value < least) {
        return (least);
    }
    if (value > most) {
        return (most);
    }
    return (value);
}

// The player has `amount` of `resource` (always, at 0).
bool crucibleHubHas(int resource = 0, int amount = 0) {
    if (amount <= 0) {
        return (true);
    }
    return (xsPlayerAttribute(1, resource) >= amount);
}

void crucibleHubRefund(int resource = 0, int amount = 0) {
    if (amount > 0) {
        xsSetPlayerAttribute(1, resource, xsPlayerAttribute(1, resource) + amount);
    }
}
"""


def _cap(upgrade: meta.Upgrade, opened: dict[int, str]) -> str:
    """XS for the levels an upgrade has on offer: all of them, or as many as its open tiers allow (`caps`)."""
    if not upgrade.caps:
        return str(upgrade.levels)

    expression = "0"

    for tier, levels in sorted(upgrade.caps):
        expression = f"crucibleHubPick({opened[tier]}, {levels}, {expression})"

    return expression


def _texts(upgrades) -> list[str]:
    """XS: an upgrade's tooltip by levels bought (`Upgrade.texts`), as crucibleHubText<n>(level)."""
    lines = []

    for n, u in enumerate(upgrades):
        if not u.texts:
            continue

        lines.append(f"string crucibleHubText{n}(int level = 0) {{")
        for level, text in enumerate(u.texts[:-1]):
            lines += [f"    if (level == {level}) {{", f'        return ("{text}");', "    }"]
        lines += [f'    return ("{u.texts[-1]}");', "}", ""]

    return lines


def xs(ctx, techs: dict[str, int]) -> str:
    """The rule that works out what's on offer (module docstring)."""
    upgrades, places = meta.UPGRADES, meta.PLACES
    level = {u.key: f"l{n}" for n, u in enumerate(upgrades)}
    opened = {1: "true", **{tier: f"t{tier}" for tier in range(2, len(meta.TIERS) + 2)}}
    reset = _variable_id(ctx, RESET_VARIABLE)
    lines = [
        XS_HELPERS,
        "int crucibleHubPick(bool use = false, int value = 0, int otherwise = 0) {",
        "    if (use) {",
        "        return (value);",
        "    }",
        "    return (otherwise);",
        "}",
        "",
        *_texts(upgrades),
        "rule crucibleHubInit",
        "    active",
        "    highFrequency",
        "{",
        f'    crucibleHubLast = xsArrayCreateInt({len(upgrades) + len(places)}, -1, "crucible hub last");',
        "    xsDisableSelf();",
        "}",
        "",
        "rule crucibleHub",
        "    active",
        "    minInterval 1",
        "{",
        "    if (xsGetTime() < 2) {",
        "        return;  // the bank's load and the stockpile come first",
        "    }",
        "",
    ]
    lines += [f"    int {level[u.key]} = xsTriggerVariable({_variable_id(ctx, u.key)});" for u in upgrades]
    refund = [
        f"        crucibleHubRefund({XS_RESOURCES[r]}, {level[u.key]} * {u.cost[r]});"
        for u in upgrades
        for r in range(4)
        if u.cost[r]
    ]
    lines += [
        "",
        f"    if (xsTriggerVariable({reset}) == 1) {{  // reset: the refund, then the triggers clear it",
        *refund,
        f"        xsSetTriggerVariable({reset}, 2);",
        "        return;",
        "    }",
        "",
        f"    bool open = (xsTriggerVariable({reset}) == 0);  // not reset",
        f"    int bought = {' + '.join(level[u.key] for u in upgrades)};",
    ]
    lines += [f"    bool {opened[n + 2]} = (bought >= {sum(meta.TIERS[: n + 1])});" for n in range(len(meta.TIERS))]
    lines += [
        f"    xsSetPlayerAttribute({TIER_COUNTERS[n]}, {RELICS}, "
        f"crucibleHubBetween(bought - {sum(meta.TIERS[:n])}, 0, {need}));"
        for n, need in enumerate(meta.TIERS)
    ]

    def place_open(p: meta.Place) -> str:
        parts = [opened[max(p.tier, 1)]] + ([f"({level[p.opened_by]} >= 1)"] if p.opened_by else [])

        return " && ".join(parts)

    for n, u in enumerate(upgrades):
        lines.append(f"    int c{n} = {_cap(u, opened)};")
        parts = [
            "open",
            f"({level[u.key]} < c{n})",
            f"({place_open(meta.place(u.place))})",
            opened[meta.tier_of(u)],
            *(f"({level[key]} >= {need})" for key, need in u.requires),
        ]
        lines.append(f"    bool o{n} = {' && '.join(parts)};")
        afford = " && ".join(f"crucibleHubHas({XS_RESOURCES[r]}, {u.cost[r]})" for r in range(4))
        lines.append(f"    bool a{n} = o{n} && {afford};")

    lines += [f"    int s{n} = crucibleHubState(o{n}, {level[u.key]});" for n, u in enumerate(upgrades)]
    lines.append("")

    for n, u in enumerate(upgrades):
        variable = _variable_id(ctx, _state_variable(u))
        name = f'"{u.title} (" + {level[u.key]} + "/" + c{n} + ")"'
        lines.append(f"    if (crucibleHubSend({n}, {variable}, s{n})) {{")
        lines.append(f"        xsSetTechName({techs[u.tech]}, 1, {name});")
        if u.texts:
            lines.append(f"        xsSetTechDescription({techs[u.tech]}, 1, crucibleHubText{n}({level[u.key]}));")
        lines.append("    }")

    for k, p in enumerate(places):
        mine = [n for n, u in enumerate(upgrades) if u.place == p.key]
        offered = " || ".join(f"o{n}" for n in mine) or "false"
        affordable = " || ".join(f"a{n}" for n in mine) or "false"
        variable = _variable_id(ctx, _place_variable(p))
        send = f"crucibleHubSignal({len(upgrades) + k}, {variable}, crucibleHubPlace({offered}, {affordable}));"
        lines.append(f"    if ({place_open(p)}) {{ {send} }}")

    lines.append("}")

    return "\n".join(lines) + "\n"


def build(out: Path, techs: dict[str, int]) -> Path:
    """`techs`: the Crucible data mod's manifest."""
    o = SESSIONS.open(asset("hub"))
    s = o.scenario

    try:
        with games.use("ror"):
            buildings = _setup(o, techs)
            plan = _plan(s, buildings)

            for player, (x, y) in zip(meta.TIER_PLAYERS.values(), KEEPERS, strict=True):  # after the plan
                s.unit_manager.add_unit(player=player, unit_const=KEEPER, x=x, y=y)

            ctx = blocks.Ctx(s)
            _start(ctx, techs)
            _reset(ctx)

            for upgrade in meta.UPGRADES:
                _upgrade(ctx, upgrade, techs[upgrade.tech], plan.get(upgrade.key, []), techs)

            _tier_objectives(ctx, s)

            for place in meta.PLACES:
                _place_triggers(ctx, place, buildings[place.key])

            ctx.xs(xs(ctx, techs))
            datamod_check.add(ctx, techs[meta.UPGRADES[0].tech], player=PLAYER)
            ctx.flush_xs()

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
