"""Test: melee waves against bad wall setups, with the wall-breaker (scenarios/breaker.py) on player 2.

Player 1 owns the walls and what they guard; players 2 and 3 are the enemy, each group attack-moving at its target 5
seconds in. Player 2 has the breaker (it says each order in the chat); player 3 doesn't, as the control.

A  a Watch Tower walled in all round (player 2): Axemen and Cavalry should break a segment and kill it.
A' the same tower and units for player 3, no breaker: expect them to stand at the wall.
B  a house inside two rings of wall: Swordsmen and War Elephants should break through both.
C  a long wall with a way round its west end: Clubmen and a Scout should walk round, not break it.
D  a house in a big walled square, a larger mixed group: they should gather on a segment or two, not spread out.
E  a Watch Tower and two Bowmen walled in by a ring of houses: they should break a house, then kill what's inside.
F  four Bowmen in a pocket of Barracks, Granaries and Storage Pits: they should break a building to reach them.

Buildings walling (E, F) are placed on their own grid (a 2x2 house's centre on a tile corner, a 3x3's on a tile
centre) so they touch with no gap.
"""

from aoe2ed import tables

from crucible.scenarios import breaker

NAME = "walls"
BOONS: tuple[str, ...] = ()
BUTTONS: dict[str, int] = {}
PLAYERS = 3
SIZE = 120
OWNER, BREAKER, CONTROL = 1, 2, 3
SMALL_WALL = "small_wall"
ATTACK_MOVE = 17

Tile = tuple[int, int]


def ring(center: Tile, radius: int) -> list[Tile]:
    """The square ring of tiles `radius` from `center`."""
    cx, cy = center
    r = radius

    return [
        (x, y)
        for x in range(cx - r, cx + r + 1)
        for y in range(cy - r, cy + r + 1)
        if max(abs(x - cx), abs(y - cy)) == r
    ]


def box(x0: int, y0: int, x1: int, y1: int) -> list[Tile]:
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) if x in (x0, x1) or y in (y0, y1)]


def row(x0: int, x1: int, y: int) -> list[Tile]:
    return [(x, y) for x in range(x0, x1 + 1)]


SETUPS = (  # name, attacker, guarded (unit, tile), walls, attackers (unit, count), spawn centre
    ("A", BREAKER, ("watch_tower", (22, 22)), ring((22, 22), 2), (("axeman", 4), ("cavalry", 2)), (22, 40)),
    ("A'", CONTROL, ("watch_tower", (48, 22)), ring((48, 22), 2), (("axeman", 4), ("cavalry", 2)), (48, 40)),
    (
        "B",
        BREAKER,
        ("house", (78, 22)),
        ring((78, 22), 3) + ring((78, 22), 5),
        (("short_swordsman", 3), ("war_elephant", 2)),
        (78, 44),
    ),
    ("C", BREAKER, ("house", (40, 58)), row(8, 62, 66), (("clubman", 5), ("scout", 1)), (40, 85)),
    (
        "D",
        BREAKER,
        ("house", (87, 69)),
        box(78, 60, 96, 78),
        (("axeman", 4), ("cavalry", 3), ("hoplite", 3)),
        (87, 98),
    ),
)


def houses(center: Tile, k: int) -> list[Tile]:
    """2x2 houses in a closed square ring `k` houses out from `center` (a tile corner)."""
    cx, cy = center

    return [(cx + 2 * i, cy + 2 * j) for i in range(-k, k + 1) for j in range(-k, k + 1) if max(abs(i), abs(j)) == k]


def blocks(center: Tile) -> list[Tile]:
    """3x3 buildings in a closed ring round `center` (a tile): eight of them, three tiles apart."""
    cx, cy = center

    return [(cx + 3 * i, cy + 3 * j) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0)]


POCKET = ("barracks", "granary", "storage_pit")
LABELS = {  # the caption over each setup's guarded building
    "A": "A: walled-in tower (breaker)",
    "A'": "A': walled-in tower (no breaker)",
    "B": "B: two rings of wall",
    "C": "C: wall with a way round",
    "D": "D: big walled square",
    "E": "E: tower ringed by houses",
    "F": "F: archers in a building pocket",
}
BUILT = (  # name, guarded: [(unit, x, y)] placed exactly, attackers, spawn centre, target
    (
        "E",
        [("watch_tower", 20.0, 100.0), ("bowman", 18.0, 100.0), ("bowman", 22.0, 100.0)]
        + [("house", float(x), float(y)) for x, y in houses((20, 100), 2)],
        (("axeman", 4), ("cavalry", 2), ("clubman", 2)),
        (20, 114),
        (20, 100),
    ),
    (
        "F",
        [("bowman", 54.5 + n % 2 * 2, 99.5 + n // 2 * 2) for n in range(4)]
        + [(POCKET[n % 3], x + 0.5, y + 0.5) for n, (x, y) in enumerate(blocks((55, 100)))],
        (("short_swordsman", 3), ("scout", 2), ("axeman", 3)),
        (55, 114),
        (55, 100),
    ),
)


def _attack(ctx, name: str, attacker: int, group, spawn: Tile, target: Tile) -> None:
    from crucible.scenarios.check import add_unit

    sx, sy = spawn
    units = [kind for kind, count in group for _ in range(count)]

    for n, kind in enumerate(units):
        add_unit(ctx.scenario, kind, sx - len(units) + 2 * n, sy, player=attacker)

    ctx.trigger(
        f"Walls {name}: attack",
        [{"type": "timer", "timer": 5}],
        [
            {
                "type": "task_object",
                "source_player": attacker,
                "area": [sx - len(units) - 1, sy - 2, sx + len(units) + 1, sy + 2],
                "action_type": ATTACK_MOVE,
                "location": list(target),
            }
        ],
    )


def setup(o, ctx, techs: dict[str, int], top: int) -> str:
    from aoe2ed.tools.world import diplomacy_set

    from crucible.scenarios.check import add_unit

    s = o.scenario
    diplomacy_set(o.handle, OWNER, [BREAKER, CONTROL], "ENEMY")
    diplomacy_set(o.handle, BREAKER, [CONTROL], "ALLY")

    labels = []

    for name, attacker, (unit, (gx, gy)), walls, group, spawn in SETUPS:
        labels.append((name, add_unit(s, unit, gx, gy, player=OWNER)))

        for x, y in walls:
            add_unit(s, SMALL_WALL, x, y, player=OWNER)

        _attack(ctx, name, attacker, group, spawn, (gx, gy))

    for name, guarded, group, spawn, target in BUILT:
        for unit, x, y in guarded:
            placed = s.unit_manager.add_unit(player=OWNER, unit_const=tables.object_id(unit.upper(), "ror"), x=x, y=y)

            if unit != "bowman" and not any(n == name for n, _ in labels):  # the first building
                labels.append((name, placed.reference_id))

        _attack(ctx, name, BREAKER, group, spawn, target)

    ctx.trigger(
        "Walls: labels",
        [],
        [
            {
                "type": "change_object_caption",
                "source_player": OWNER,
                "selected_object_ids": [ref],
                "message": LABELS[n],
            }
            for n, ref in labels
        ],
    )
    ctx.xs(breaker.xs(BREAKER, (OWNER,), chat=True))

    return (
        "WALLS (melee against walls; player 2 has the wall-breaker, player 3 doesn't): seven setups, the groups "
        "attack-move 5 s in. A (top left): a Watch Tower walled in all round, player 2 should break in and kill it. "
        "A' (next to it): the same for player 3, no breaker: they should stand at the wall. B (top right): a house in "
        "two rings, both should be broken. C (middle left): a long wall with a way round its west end: they should "
        "walk round. D (bottom right): a house in a big walled square, a bigger group: they should gather on a "
        "segment or two. E (bottom left): a tower and two Bowmen ringed by houses: they should break a house and kill "
        "what's inside. F (next to it): four Bowmen in a pocket of Barracks, Granaries and Storage Pits: they should "
        "break in. The chat says each breaker order."
    )
