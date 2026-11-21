from aoe2ed import xs

from crucible.scenarios import breaker
from crucible.scenarios.checks import walls


def test_breaker_xs_checks():
    assert xs.check(breaker.xs(3, (1, 5)))["ok"]
    assert xs.check(breaker.xs(2, (1,), chat=True))["ok"]


def test_wall_setups_are_closed_where_they_should_be():
    tower = walls.ring((22, 22), 2)

    assert len(tower) == 16  # a full ring round the tower
    assert len(set(walls.box(78, 60, 96, 78))) == 2 * (19 + 17)
