"""The engine test map: one Return of Rome scenario that answers what the Crucible design depends on.

Each part tests one question, with a control beside it, so one playthrough settles them all. Directions are as
seen in game: tile (0, 0) is the left corner, x runs to the top corner, y to the bottom corner.

- **Top-left edge: ground you can walk on but can't build on.** Strips of the terrains RoR's data says take no
  buildings (Rock 1, Quicksand, Bogland, Beach, Swamp, Shallows, Ice). Your villagers start below them with
  resources: try to place buildings on each strip, and walk across to feel whether any slow units down.
- **Left (the starting view): a spawn safe zone.** Your units stand inside a road-bordered square. Every second, a trigger makes
  all your units attackable again, then the ones inside the square unattackable. At 0:20 an enemy army
  (swordsmen, bowmen, stone throwers) attack-moves into it. Two hoplites wait outside the square as the control.
- **Bottom: resource amounts.** Row A berry bushes are set to 200 food each (Modify Object Attribute over an
  area); row B is left as the control. Gold mines are all set to 50 (Modify Attribute on the gold mine type,
  to see whether a type-wide change reaches mines already on the map). Stone mines are set to 75 per object.
- **Right: formations.** Two allied groups of the same units: at 0:30 group A is told to take a line formation
  and march to the top corner as one group; group B just moves. At 1:30 group A takes a box formation and marches back.

The map is revealed, so you can watch everything, and nothing ends the game.
"""
from __future__ import annotations

from pathlib import Path

from aoe2ed import blocks, games
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import diplomacy_set, options_set, player_set

SIZE = 96
NAME = "crucible_engine_test"
GRASS = 0
ROAD = 24
# Terrains RoR's data marks walkable for villagers but closed to buildings (scripts: gen_civ_bonuses' terrain scan,
# 2026-11-06): no buildings at all on Rock 1, Quicksand and Bogland; walls or docks still fit on some others.
NO_BUILD = {"Rock 1": 40, "Quicksand": 46, "Bogland": 101, "Beach": 2, "Swamp": 111, "Shallows": 4, "Ice": 35}
STRIP_W, STRIP_GAP, STRIPS_X, STRIPS_Y = 8, 2, 6, (4, 20)
SAFE = (8, 40, 23, 55)                     # the spawn safe zone (x1, y1, x2, y2), inclusive
BUSHES_A, BUSHES_B = (40, 72, 50, 76), (40, 80, 50, 84)
FOOD_A, GOLD_ALL, STONE_EACH = 200, 50, 75
FORMATION_A, FORMATION_B = (70, 40, 78, 46), (82, 40, 90, 46)
LINE_FORMATION, BOX_FORMATION, MOVE = 18, 19, 1           # Task Object action types
STORAGE_1 = 21                                            # object attribute: amount of 1st resource storage
SET = 1                                                   # Operation.SET
REVEAL_MAP = 203                    # player resource: 2 = whole map visible (engine facts; unnamed in the parser)

INSTRUCTIONS = """Crucible engine test. The map is revealed; nothing ends the game.

SAFE ZONE (where you start, the road square): your units inside can't be attacked. At 0:20 an enemy army marches \
in. Do units inside take damage (stone thrower splash too)? Do your two hoplites outside the square get attacked? \
Walk a unit out of the square: is it attackable within a second?

CAN'T BUILD, CAN WALK (the coloured strips along the top-left edge of the map; from the left corner up): Rock 1, \
Quicksand, Bogland, Beach, Swamp, Shallows, Ice. Try to place buildings on each (your villagers below them have \
resources), and walk them across: does any strip slow them?

RESOURCES (toward the bottom corner): select a bush or mine to see its amount. Upper bush row: 200 food. Lower \
bush row: untouched. Gold mines: 50 (type-wide change). Stone mines: 75 (per object).

FORMATIONS (the two allied groups toward the right): at 0:30 the group nearer the middle marches to the top \
corner in a line formation while the other just moves. At 1:30 the first group marches back in a box formation. \
Do they keep formation?"""


def _paint(s, terrain: int, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    mm = s.map_manager
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            mm.get_tile(x=x, y=y).terrain_id = terrain


def _outline(s, terrain: int, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    for x in range(x1 - 1, x2 + 2):
        _paint(s, terrain, (x, y1 - 1, x, y1 - 1))
        _paint(s, terrain, (x, y2 + 1, x, y2 + 1))
    for y in range(y1, y2 + 1):
        _paint(s, terrain, (x1 - 1, y, x1 - 1, y))
        _paint(s, terrain, (x2 + 1, y, x2 + 1, y))


def _add(s, player: int, unit: str, x: float, y: float) -> int:
    from aoe2ed import tables
    oid = tables.object_id(unit, "ror")
    if oid is None:
        raise KeyError(f"no RoR object {unit}")
    return s.unit_manager.add_unit(player=player, unit_const=oid, x=x + 0.5, y=y + 0.5).reference_id


def _row(s, player: int, unit: str, xs, y: float) -> list[int]:
    return [_add(s, player, unit, x, y) for x in xs]


def strips() -> dict[str, tuple[int, int, int, int]]:
    """Each no-build terrain's strip on the map."""
    out = {}
    for i, name in enumerate(NO_BUILD):
        x1 = STRIPS_X + i * (STRIP_W + STRIP_GAP)
        out[name] = (x1, STRIPS_Y[0], x1 + STRIP_W - 1, STRIPS_Y[1])
    return out


def build(out: Path) -> Path:
    """Write the test scenario to `out` (a folder) and return its path."""
    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario
    try:
        with games.use("ror"):
            _paint(s, GRASS, (0, 0, SIZE - 1, SIZE - 1))
            s.player_manager.active_players = 3
            for p, civ in ((1, "GREEK"), (2, "HITTITE"), (3, "ROMAN")):
                fields = {"civilization": civ, "food": 2000, "wood": 2000, "gold": 2000, "stone": 2000,
                          "population_cap": 200, "human": p == 1}
                if p > 1:
                    fields["ai"] = "none"                      # trigger-driven: no AI script acts on its own
                player_set(o.handle, p, fields)
            diplomacy_set(o.handle, 1, [2], "ENEMY")
            diplomacy_set(o.handle, 3, [1, 2], "ALLY")
            options_set(o.handle, {"victory_condition": "CUSTOM"})
            ctx = blocks.Ctx(s)

            # North: no-build strips, villagers just below.
            for name, area in strips().items():
                _paint(s, NO_BUILD[name], area)
            _row(s, 1, "VILLAGER_MALE", range(8, 70, 10), 23)

            # West: safe zone with units inside, a control pair outside, an enemy army to the east.
            _outline(s, ROAD, SAFE)
            _row(s, 1, "HOPLITE", range(10, 18, 2), 44)
            _row(s, 1, "VILLAGER_MALE", range(10, 16, 2), 48)
            _row(s, 1, "BOWMAN", (18,), 48)
            _row(s, 1, "HOPLITE", (30, 32), 47)                # the control: outside the zone
            army = (_row(s, 2, "SHORT_SWORDSMAN", range(50, 62, 2), 44) + _row(s, 2, "BOWMAN", range(50, 58, 2), 48)
                    + _row(s, 2, "STONE_THROWER", (52, 56), 52))
            _add(s, 1, "TOWN_CENTER", 86, 86)                  # keeps player 1 alive whatever happens
            blocks.anchor(ctx, player=2, at=(94, 94))
            blocks.anchor(ctx, player=3, at=(1, 94))
            x1, y1, x2, y2 = SAFE
            ctx.trigger("Safe zone", [{"type": "timer", "timer": 1}], [
                {"type": "enable_unit_attackable", "source_player": 1, "area": [0, 0, SIZE - 1, SIZE - 1]},
                {"type": "disable_unit_attackable", "source_player": 1, "area": [x1, y1, x2, y2]}],
                looping=True)
            ctx.trigger("Enemy attack", [{"type": "timer", "timer": 20}], [
                {"type": "attack_move", "source_player": 2, "selected_object_ids": army,
                 "location": [(x1 + x2) // 2, (y1 + y2) // 2]}])

            # South: resource amounts.
            _row(s, 0, "FORAGE_BUSH", (42, 44, 46, 48), BUSHES_A[1] + 2)        # row A: set to 200 food
            _row(s, 0, "FORAGE_BUSH", (42, 44, 46, 48), BUSHES_B[1] + 2)        # row B: untouched
            _row(s, 0, "GOLD_MINE", (56, 59, 62), 74)
            stone = _row(s, 0, "STONE_MINE", (56, 59, 62), 80)
            ctx.trigger("Resource amounts", [], [
                {"type": "modify_object_attribute", "source_player": 0, "object_list_unit_id": "FORAGE_BUSH",
                 "area": list(BUSHES_A), "object_attributes": STORAGE_1, "operation": SET, "quantity": FOOD_A},
                {"type": "modify_attribute", "source_player": 0, "object_list_unit_id": "GOLD_MINE",
                 "object_attributes": STORAGE_1, "operation": SET, "quantity": GOLD_ALL},
                {"type": "modify_object_attribute", "source_player": 0, "selected_object_ids": stone,
                 "object_attributes": STORAGE_1, "operation": SET, "quantity": STONE_EACH}])

            # East: formations.
            group_a = [*_row(s, 3, "HOPLITE", range(70, 79, 2), 41), *_row(s, 3, "BOWMAN", range(70, 79, 2), 44)]
            group_b = [*_row(s, 3, "HOPLITE", range(82, 91, 2), 41), *_row(s, 3, "BOWMAN", range(82, 91, 2), 44)]
            ctx.trigger("Formation out", [{"type": "timer", "timer": 30}], [
                {"type": "task_object", "source_player": 3, "selected_object_ids": group_a,
                 "action_type": LINE_FORMATION},
                {"type": "task_object", "source_player": 3, "selected_object_ids": group_a, "action_type": MOVE,
                 "location": [74, 8], "issue_group_command": 1},
                {"type": "task_object", "source_player": 3, "selected_object_ids": group_b, "action_type": MOVE,
                 "location": [86, 8]}])
            ctx.trigger("Formation back", [{"type": "timer", "timer": 90}], [
                {"type": "task_object", "source_player": 3, "selected_object_ids": group_a,
                 "action_type": BOX_FORMATION},
                {"type": "task_object", "source_player": 3, "selected_object_ids": group_a, "action_type": MOVE,
                 "location": [74, 60], "issue_group_command": 1}])

            ctx.trigger("Reveal map", [], [{"type": "modify_resource", "tribute_list": REVEAL_MAP,
                                           "source_player": 1, "quantity": 2, "operation": "SET"}])
            s.message_manager.instructions = INSTRUCTIONS
            player_set(o.handle, 1, {"initial_player_view_x": 30, "initial_player_view_y": 45})
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)
        return path
    finally:
        SESSIONS.close(o.handle)
