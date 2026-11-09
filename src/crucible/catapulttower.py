"""A stuck-together catapult tower: every tower you own fires a Stone Thrower's stone with its damage.

A standalone scenario, `crucible_catapult_tower`, to look at. A trigger changes each of player 1's tower types
(Watch, Sentry, Guard and Ballista Tower) for the whole type, so towers already on the map and any you build are
catapult towers:
- projectile: the catapult stone (656), arced;
- attack: 50 melee and +140 vs buildings, the arrow's pierce set to 0 (the Stone Thrower's);
- reload 5.4 s, range 10;
- splash width 0.8 at Blast Attack Level 6 (splash hits enemies only: the friendly fire fix).

Passive enemies and an enemy Barracks stand in range; you have villagers and resources to build more towers.
"""
from __future__ import annotations

from pathlib import Path

from aoe2ed import blocks, games, tables
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

NAME = "crucible_catapult_tower"
SIZE = 48
TOWERS = ("WATCH_TOWER", "SENTRY_TOWER", "GUARD_TOWER", "BALLISTA_TOWER")
ATTACK, RELOAD, MAX_RANGE, SHOWN_RANGE, PROJECTILE_UNIT, BLAST_WIDTH, BLAST_LEVEL = 9, 10, 12, 47, 16, 22, 44
CATAPULT_STONE = 656
PIERCE, MELEE, BUILDINGS = 3, 4, 11                # attack classes
STONE_THROWER = {"melee": 50, "buildings": 140, "reload": 5.375, "range": 10, "blast": 0.8, "level": 6}
REVEAL_MAP, SET = 203, 1

INSTRUCTIONS = """Crucible catapult tower. Every tower you own now fires a Stone Thrower's stone, with its damage \
(50 melee, +140 vs buildings), reload and range, and splash that only hurts enemies. Towers you build are catapult \
towers too. Enemies don't fight back; the enemy Barracks shows the building bonus. Nothing ends the game."""


def _add(s, player: int, unit: str | int, x: float, y: float) -> int:
    oid = unit if isinstance(unit, int) else tables.object_id(unit, "ror")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def tower_effects(player: int = 1, towers=TOWERS) -> list[dict]:
    """Trigger effects that turn each tower type into a catapult tower for `player`."""
    out = []
    v = STONE_THROWER
    for tower in towers:
        mod = {"type": "modify_attribute", "source_player": player, "object_list_unit_id": tower, "operation": SET}
        out += [
            {**mod, "object_attributes": PROJECTILE_UNIT, "quantity": CATAPULT_STONE},
            {**mod, "object_attributes": ATTACK, "armour_attack_class": MELEE, "armour_attack_quantity": v["melee"]},
            {**mod, "object_attributes": ATTACK, "armour_attack_class": BUILDINGS,
             "armour_attack_quantity": v["buildings"]},
            {**mod, "object_attributes": ATTACK, "armour_attack_class": PIERCE, "armour_attack_quantity": 0},
            {**mod, "object_attributes": RELOAD, "quantity": v["reload"]},
            {**mod, "object_attributes": MAX_RANGE, "quantity": v["range"]},
            {**mod, "object_attributes": SHOWN_RANGE, "quantity": v["range"]},
            {**mod, "object_attributes": BLAST_WIDTH, "quantity": v["blast"]},
            {**mod, "object_attributes": BLAST_LEVEL, "quantity": v["level"]},
        ]
    return out


def build(out: Path) -> Path:
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            s.player_manager.active_players = 2
            player_set(o.handle, 1, {"civilization": "GREEK", "starting_age": "IMPERIAL", "human": True,
                                     "food": 2000, "wood": 2000, "gold": 2000, "stone": 2000,
                                     "population_cap": 200})
            player_set(o.handle, 2, {"civilization": "PERSIAN", "starting_age": "IMPERIAL", "ai": "none"})
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)
            for k, tower in enumerate(TOWERS):
                _add(s, 1, tower, 10 + k * 8, 14)
            for i in range(5):
                _add(s, 1, "VILLAGER_MALE", 8 + i * 2, 8)
            _add(s, 1, "TOWN_CENTER", 4, 4)
            enemies = [_add(s, 2, "CLUBMAN", 9 + k * 8 + dx, 21 + dy)
                       for k in range(len(TOWERS)) for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
            enemies += [_add(s, 2, "WAR_ELEPHANT", 14 + k * 8, 22) for k in range(3)]
            _add(s, 2, "BARRACKS", 26, 22)
            blocks.anchor(ctx, player=2, at=(46, 46))
            ctx.trigger("Catapult towers", [], [
                *tower_effects(1),
                {"type": "change_object_stance", "source_player": 2, "selected_object_ids": enemies,
                 "attack_stance": "NO_ATTACK_STANCE"},
                {"type": "modify_resource", "tribute_list": REVEAL_MAP, "source_player": 1, "quantity": 2,
                 "operation": "SET"}])
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 20, "initial_player_view_y": 16})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)
