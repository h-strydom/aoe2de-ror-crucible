"""crucible_arena: the run map, built from the hand-made layout in assets/map_crucible.aoe2scenario.

The layout holds a Greek base (player 3: the Wonder, walls and four roads out: west, east and two north-west) with
its decoration (gaia; its trees are left out), and an enemy base on the west edge (player 1's walls and buildings,
player 2's army, a road). The arena centres the Greek base on the Wonder and puts a copy of the enemy base on the map
edge at the end of each road, turned to face the centre. The two north-west bases
overlap: anything of the second on a taken tile is dropped. The biggest attacks are to come from the north-west.
"""

from dataclasses import dataclass
from pathlib import Path

from aoe2ed import games
from aoe2ed.render.colors import building_size, object_class
from aoe2ed.session import SESSIONS
from aoe2ed.tools.world import options_set, player_set

from crucible.datamod.civs import PLAYER, SCENARIO_CIVS, Style

ROOT = Path(__file__).resolve().parents[3]
LAYOUT = ROOT / "assets" / "map_crucible.aoe2scenario"
NAME = "crucible_arena"
SIZE = 220
GROUND = 76  # the layout's plain terrain: everything else is copied

CENTRE = (74, 98, 134, 165)  # the Greek base, its roads and decoration: x0, y0, x1, y1 (inclusive)

# The players, coloured as in the layout (colours: 1 red, 5 purple, 6 gray, 7 orange). Still to come: the player's
# neutral allies (gray) and raiders (any other colour).
HUMAN, INVULNERABLE_ENEMY, VULNERABLE_ENEMY = 1, 2, 3
PLAYERS = {  # player -> (civ, colour)
    HUMAN: (SCENARIO_CIVS[PLAYER], 5),  # the player (purple)
    INVULNERABLE_ENEMY: (SCENARIO_CIVS[Style.ROMAN], 7),  # the enemy bases (orange)
    VULNERABLE_ENEMY: (SCENARIO_CIVS[Style.ROMAN], 1),  # the enemy army (red)
}
LAYOUT_PLAYERS = {3: HUMAN, 1: INVULNERABLE_ENEMY, 2: VULNERABLE_ENEMY, 0: 0}  # layout player -> arena player
CENTRE_PLAYERS = (3, 0)  # in the layout: the Greek base and the decoration
WONDER = 276
ENEMY = (0, 112, 20, 150)  # inside the enemy base's walls (the buildings outside are left out)
ENEMY_PLAYERS = (1, 2)  # in the layout: the enemy base's buildings and its army
ENEMY_ROAD = 130.5  # the middle of its road out (tiles 129-131)

# the Greek base's roads after centring, as the line through their middle; each gets an enemy base
ROADS = (  # (edge, middle of the road)
    ("north-west", 100.5),
    ("north-west", 118.5),
    ("west", 109.5),
    ("east", 109.5),
)


@dataclass(frozen=True)
class Piece:
    unit: int
    x: float
    y: float
    rotation: float


def _pieces(layout, box: tuple[int, int, int, int], players) -> dict[int, list[Piece]]:
    """The players' units in the box, trees left out."""
    x0, y0, x1, y1 = box
    found: dict[int, list[Piece]] = {}

    for player in players:
        for u in layout.unit_manager.units[player]:
            if x0 <= u.x <= x1 + 1 and y0 <= u.y <= y1 + 1 and object_class(u.unit_const) != "tree":
                found.setdefault(player, []).append(Piece(u.unit_const, u.x, u.y, u.rotation))

    return found


def _terrain(layout, box: tuple[int, int, int, int]) -> list[tuple[int, int, int]]:
    """(x, y, terrain) of every tile in the box that isn't plain ground."""
    n, (x0, y0, x1, y1) = layout.map_manager.map_size, box
    tiles = layout.map_manager.terrain

    return [
        (x, y, tiles[y * n + x].terrain_id)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if tiles[y * n + x].terrain_id != GROUND
    ]


def _place(edge: str, road: float, x: float, y: float) -> tuple[float, float]:
    """An enemy-base point (x from its edge, y along it) on `edge`, its road meeting `road`."""
    across = y - ENEMY_ROAD

    if edge == "west":
        return x, road + across

    if edge == "east":  # turned half way round
        return SIZE - x, road - across

    return road - across, x  # north-west: turned a quarter


class Arena:
    """Places pieces, base by base: a piece is dropped if it would land on a tile an earlier base took (pieces of
    one base may sit as close as the layout has them)."""

    def __init__(self, scenario) -> None:
        self.scenario = scenario
        self.taken: set[tuple[int, int]] = set()  # by earlier bases
        self.base: set[tuple[int, int]] = set()  # by the base being placed

    def _tiles(self, unit: int, x: float, y: float) -> set[tuple[int, int]]:
        size = building_size(unit) or 1
        left, top = int(x - size / 2 + 0.5), int(y - size / 2 + 0.5)

        return {(left + i, top + j) for i in range(size) for j in range(size)}

    def add(self, player: int, piece: Piece, x: float, y: float) -> bool:
        tiles = self._tiles(piece.unit, x, y)

        if tiles & self.taken or not all(0 <= tx < SIZE and 0 <= ty < SIZE for tx, ty in tiles):
            return False

        self.base |= tiles
        self.scenario.unit_manager.add_unit(player=player, unit_const=piece.unit, x=x, y=y, rotation=piece.rotation)

        return True

    def next_base(self) -> None:
        self.taken |= self.base
        self.base = set()

    def paint(self, x: int, y: int, terrain: int) -> None:
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.scenario.map_manager.terrain[y * SIZE + x].terrain_id = terrain


def build(out: Path) -> Path:
    layout_session = SESSIONS.open(LAYOUT)
    layout = layout_session.scenario
    wonder = next(u for u in layout.unit_manager.units[3] if u.unit_const == WONDER)
    dx, dy = round(SIZE / 2 - 0.5 - wonder.x), round(SIZE / 2 - 0.5 - wonder.y)  # 5x5 Wonder: centre tile 109
    centre_units, centre_tiles = _pieces(layout, CENTRE, CENTRE_PLAYERS), _terrain(layout, CENTRE)
    enemy_units, enemy_tiles = _pieces(layout, ENEMY, ENEMY_PLAYERS), _terrain(layout, ENEMY)
    SESSIONS.close(layout_session.handle)

    o = SESSIONS.new(SIZE, game="ror")
    s = o.scenario

    try:
        with games.use("ror"):
            for tile in s.map_manager.terrain:
                tile.terrain_id = GROUND

            s.player_manager.active_players = len(PLAYERS)

            for player, (civ, colour) in PLAYERS.items():
                human = player == HUMAN
                fields = {"civilization": civ, "color": colour, "human": human}
                player_set(o.handle, player, fields if human else fields | {"ai": "none"})

            options_set(o.handle, {"victory_condition": "CUSTOM"})
            arena = Arena(s)

            for x, y, terrain in centre_tiles:
                arena.paint(x + dx, y + dy, terrain)

            for layout_player, pieces in centre_units.items():
                for piece in pieces:
                    arena.add(LAYOUT_PLAYERS[layout_player], piece, piece.x + dx, piece.y + dy)

            arena.next_base()

            for edge, road in ROADS:
                for x, y, terrain in enemy_tiles:
                    px, py = _place(edge, road, x + 0.5, y + 0.5)
                    arena.paint(int(px), int(py), terrain)

                for layout_player, pieces in enemy_units.items():
                    for piece in pieces:
                        arena.add(LAYOUT_PLAYERS[layout_player], piece, *_place(edge, road, piece.x, piece.y))

                arena.next_base()

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
