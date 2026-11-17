"""crucible_run: the arena as a game (docs/arena.md), built from the hand-made map (assets/crucible_arena).

So far: the five factions and their diplomacy, the player's base handed to the Allies (the player keeps the Town
Center and the Wonder, with standard resources and 4 villagers; the Allies' buildings start at 1 HP, their walls
randomly damaged), the City States made invulnerable, the waves (staged, then sent: waves.py), and defeat when the
Wonder falls. Raids and the win come later.

Played with the Crucible data mod (the Send next wave button is one of its techs).
"""

from enum import IntEnum
from pathlib import Path

from aoe2ed import blocks, games
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

from crucible.datamod.civs import SCENARIO_CIVS, Style
from crucible.datamod.mod import source_dat
from crucible.scenarios import run_xs, waves
from crucible.scenarios.arena import ARENA

NAME = "crucible_run"
TOWN_CENTER, WONDER = 109, 276
WALL_CLASSES = (27, 39)
REVEAL_MAP = 203  # resource: 2 = the whole map visible, no fog
VILLAGER_MALE, VILLAGER_FEMALE = 83, 293
STANDARD_RESOURCES = {"food": 200, "wood": 200, "gold": 0, "stone": 150}  # Return of Rome's standard start
VILLAGERS = ((107.5, 122.5), (108.5, 122.5), (110.5, 119.5), (110.5, 120.5))  # by the Town Center
META_VILLAGERS = tuple((x + 0.5, y + 0.5) for x in (104, 105) for y in (126, 127, 128))  # just south: meta unlocks


class Faction(IntEnum):
    PLAYER = 1
    CITY_STATES = 2
    LEGION = 3
    TRADERS = 4
    ALLIES = 5


PLAYERS = {  # player -> its fields
    Faction.PLAYER: {
        "tribe_name": "Player",
        "civilization": SCENARIO_CIVS[Style.GREEK],
        "color": 5,  # purple
        "starting_age": "DARK",  # Stone Age
        "human": True,
    }
    | STANDARD_RESOURCES,
    Faction.CITY_STATES: {
        "tribe_name": "City States",
        "civilization": SCENARIO_CIVS[Style.ROMAN],
        "color": 7,  # orange
        "starting_age": "IMPERIAL",  # Iron Age: looks only, they're invulnerable
    },
    Faction.LEGION: {
        "tribe_name": "Legion",
        "civilization": SCENARIO_CIVS[Style.ROMAN],
        "color": 1,  # red
        "starting_age": "DARK",  # ages up with the waves
    },
    Faction.TRADERS: {
        "tribe_name": "Traders",
        "civilization": SCENARIO_CIVS[Style.EGYPTIAN],
        "color": 6,  # gray
        "starting_age": "IMPERIAL",
    },
    Faction.ALLIES: {
        "tribe_name": "Allies",
        "civilization": SCENARIO_CIVS[Style.GREEK],
        "color": 6,  # gray
        "starting_age": "DARK",
    },
}
ENEMIES = (Faction.CITY_STATES, Faction.LEGION)
FRIENDS = (Faction.PLAYER, Faction.ALLIES)
KEEPS = (TOWN_CENTER, WONDER)  # what the player starts with


def _diplomacy(handle: str) -> None:
    others = [f for f in Faction if f != Faction.TRADERS]
    diplomacy_set(handle, Faction.TRADERS, others, "NEUTRAL")
    diplomacy_set(handle, Faction.PLAYER, [Faction.ALLIES], "ALLY")
    diplomacy_set(handle, Faction.CITY_STATES, [Faction.LEGION], "ALLY")

    for friend in FRIENDS:
        diplomacy_set(handle, friend, list(ENEMIES), "ENEMY")


def _hand_over(s) -> list[int]:
    """Give the Allies every unit of the player's but the Town Center and the Wonder; returns their unit types."""
    units = s.unit_manager.units[Faction.PLAYER]
    given = [u for u in units if u.unit_const not in KEEPS]
    s.unit_manager.change_ownership(given, Faction.ALLIES)

    return sorted({u.unit_const for u in given})


def build(out: Path, techs: dict[str, int]) -> Path:
    """`techs`: the Crucible data mod's manifest."""
    units = source_dat().civs[Style.GREEK].units
    o = SESSIONS.open(ARENA)
    s = o.scenario

    try:
        with games.use("ror"):
            s.player_manager.active_players = len(Faction)

            for player, fields in PLAYERS.items():
                ai = {} if fields.get("human") else {"ai": "none", "human": False}
                player_set(o.handle, player, fields | ai)

            _diplomacy(o.handle)
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            player_set(o.handle, Faction.PLAYER, {"initial_player_view_x": 110, "initial_player_view_y": 110})

            allied = _hand_over(s)

            for k, (x, y) in enumerate(VILLAGERS):
                villager = VILLAGER_MALE if k % 2 == 0 else VILLAGER_FEMALE
                s.unit_manager.add_unit(player=Faction.PLAYER, unit_const=villager, x=x, y=y)

            walls = {t: units[t].hit_points for t in allied if units[t].class_ in WALL_CLASSES}
            buildings = [t for t in allied if t not in walls]
            city_states = sorted({u.unit_const for u in s.unit_manager.units[Faction.CITY_STATES]})

            ctx = blocks.Ctx(s)
            ctx.xs(run_xs.start(walls, buildings, city_states, allies=Faction.ALLIES, invulnerable=Faction.CITY_STATES))
            waves.add(ctx, techs)
            ctx.flush_xs()
            ctx.trigger(
                "Shared vision",
                [],
                [
                    {
                        "type": "set_player_visibility",
                        "source_player": source,
                        "target_player": target,
                        "visibility_state": 0,  # visible
                    }
                    for source, target in ((Faction.PLAYER, Faction.ALLIES), (Faction.ALLIES, Faction.PLAYER))
                ],
            )
            ctx.trigger(
                "Full vision",  # everyone but the player and the Allies sees the whole map
                [],
                [
                    {
                        "type": "modify_resource",
                        "tribute_list": REVEAL_MAP,
                        "source_player": player,
                        "quantity": 2,
                        "operation": "SET",
                    }
                    for player in Faction
                    if player not in FRIENDS
                ],
            )
            blocks.lose_if_destroyed(
                ctx,
                player=Faction.PLAYER,
                unit_type=WONDER,
                winner=Faction.LEGION,
                name="Wonder lost",
            )

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
