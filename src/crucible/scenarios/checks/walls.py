"""Test: melee waves against bad wall setups, with the wall-breaker (scenarios/breaker.py) on player 2.

Player 1 owns the walls and what they guard; players 2 and 3 are the enemy, each group attack-moving at its target 5
seconds in. Player 2 has the breaker (it says each order in the chat); player 3 doesn't, as the control.

A  a Watch Tower walled in all round (player 2): Axemen and Cavalry should break a segment and kill it.
A' the same tower and units for player 3, no breaker: expect them to stand at the wall.
B  a house inside two rings of wall: Swordsmen and War Elephants should break through both.
C  a long wall with a way round its west end: Clubmen and a Scout should walk round, not break it.
D  a house in a big walled square, a larger mixed group: they should gather on a segment or two, not spread out.
"""

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


def setup(o, ctx, techs: dict[str, int], top: int) -> str:
    from aoe2ed.tools.world import diplomacy_set

    from crucible.scenarios.check import add_unit

    s = o.scenario
    diplomacy_set(o.handle, OWNER, [BREAKER, CONTROL], "ENEMY")
    diplomacy_set(o.handle, BREAKER, [CONTROL], "ALLY")

    for name, attacker, (unit, (gx, gy)), walls, group, (sx, sy) in SETUPS:
        add_unit(s, unit, gx, gy, player=OWNER)

        for x, y in walls:
            add_unit(s, SMALL_WALL, x, y, player=OWNER)

        units = [kind for kind, count in group for _ in range(count)]

        for n, kind in enumerate(units):
            add_unit(s, kind, sx - len(units) + 2 * n, sy, player=attacker)

        spawn = [sx - len(units) - 1, sy - 2, sx + len(units) + 1, sy + 2]
        ctx.trigger(
            f"Walls {name}: attack",
            [{"type": "timer", "timer": 5}],
            [
                {
                    "type": "task_object",
                    "source_player": attacker,
                    "area": spawn,
                    "action_type": ATTACK_MOVE,
                    "location": [gx, gy],
                }
            ],
        )

    ctx.xs(breaker.xs(BREAKER, (OWNER,), chat=True))

    return (
        "WALLS (melee against walls; player 2 has the wall-breaker, player 3 doesn't): five setups, the groups "
        "attack-move 5 s in. A (top left): a Watch Tower walled in all round, player 2 should break in and kill it. "
        "A' (next to it): the same for player 3, no breaker: they should stand at the wall. B (top right): a house in "
        "two rings, both should be broken. C (middle left): a long wall with a way round its west end: they should "
        "walk round. D (bottom right): a house in a big walled square, a bigger group: they should gather on a "
        "segment or two. The chat says each breaker order."
    )
