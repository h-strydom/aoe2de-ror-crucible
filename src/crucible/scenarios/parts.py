"""The arena's parts, each on its own blank map: the Greek base and the enemy bases (north, west, east), from the arena
as edited by hand (assets/arena_edited.aoe2scenario).

Only buildings come across, onto plain mud. Each map is square and as small as its part fits; an enemy base keeps its
side against the same edge it had in the arena (north at the top, west on the left, east on the right), the Greek base
sits in the middle.
"""

from dataclasses import dataclass
from pathlib import Path

from aoe2ed import games
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import options_set, player_set

from crucible.datamod.mod import source_dat
from crucible.scenarios.arena import HUMAN, INVULNERABLE_ENEMY, PLAYERS, ROOT

EDITED = ROOT / "assets" / "arena_edited.aoe2scenario"
MUD = 76  # Dirt Mud
BUILDING = 80  # unit type


@dataclass(frozen=True)
class Part:
    name: str
    player: int
    box: tuple[int, int, int, int]  # where it is in the arena: x0, y0, x1, y1
    snap: str  # the edge it keeps: top, left, right, or centre


PARTS = (
    Part("centre", HUMAN, (80, 80, 140, 140), "centre"),
    Part("north", INVULNERABLE_ENEMY, (60, 0, 160, 40), "top"),
    Part("west", INVULNERABLE_ENEMY, (0, 80, 40, 140), "left"),
    Part("east", INVULNERABLE_ENEMY, (180, 80, 220, 140), "right"),
)


def _footprint(size: int, x: float, y: float) -> tuple[int, int, int, int]:
    """The tiles a building covers: left, top, right, bottom (exclusive)."""
    left, top = round(x - size / 2), round(y - size / 2)

    return left, top, left + size, top + size


def _offset(snap: str, bounds: tuple[int, int, int, int], side: int) -> tuple[int, int]:
    left, top, right, bottom = bounds
    width, height = right - left, bottom - top
    centred = (-left + (side - width) // 2, -top + (side - height) // 2)

    if snap == "top":
        return centred[0], -top

    if snap == "left":
        return -left, centred[1]

    if snap == "right":
        return side - right, centred[1]

    return centred


def build(out: Path) -> list[Path]:
    units = source_dat().civs[1].units
    sizes = {i: round(2 * u.clearance_size[0]) for i, u in enumerate(units) if u and u.type == BUILDING}
    edited = SESSIONS.open(EDITED)
    paths = []

    try:
        for part in PARTS:
            x0, y0, x1, y1 = part.box
            buildings = [
                (u.unit_const, u.x, u.y, u.rotation)
                for u in edited.scenario.unit_manager.units[part.player]
                if u.unit_const in sizes and x0 <= u.x < x1 and y0 <= u.y < y1
            ]
            tiles = [_footprint(sizes[unit], x, y) for unit, x, y, _ in buildings]
            bounds = (
                min(t[0] for t in tiles),
                min(t[1] for t in tiles),
                max(t[2] for t in tiles),
                max(t[3] for t in tiles),
            )
            side = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
            dx, dy = _offset(part.snap, bounds, side)

            o = SESSIONS.new(side, game="ror")

            try:
                with games.use("ror"):
                    for tile in o.scenario.map_manager.terrain:
                        tile.terrain_id = MUD

                    o.scenario.player_manager.active_players = max(PLAYERS)

                    for player, (civ, colour) in PLAYERS.items():
                        human = player == HUMAN
                        fields = {"civilization": civ, "color": colour, "human": human}
                        player_set(o.handle, player, fields if human else fields | {"ai": "none"})

                    options_set(o.handle, {"victory_condition": "CUSTOM"})

                    for unit, x, y, rotation in buildings:
                        o.scenario.unit_manager.add_unit(
                            player=part.player,
                            unit_const=unit,
                            x=x + dx,
                            y=y + dy,
                            rotation=rotation,
                        )

                out.mkdir(parents=True, exist_ok=True)
                path = out / f"crucible_part_{part.name}.aoe2scenario"
                SESSIONS.save(o.handle, path, overwrite=True)
                paths.append(path)
            finally:
                SESSIONS.close(o.handle)
    finally:
        SESSIONS.close(edited.handle)

    return paths
