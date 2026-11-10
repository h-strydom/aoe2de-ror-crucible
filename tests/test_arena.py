from aoe2ed.session import SESSIONS

from crucible.scenarios import arena


def test_arena_centres_the_wonder_and_copies_the_bases(tmp_path):
    o = SESSIONS.open(arena.build(tmp_path))

    try:
        units = o.scenario.unit_manager.units
        wonder = next(u for u in units[arena.HUMAN] if u.unit_const == arena.WONDER)
        assert (wonder.x, wonder.y) == (109.5, 109.5)  # the centre tile of a 220 map

        layout = SESSIONS.open(arena.LAYOUT)
        enemy = [u for u in layout.scenario.unit_manager.units[1] if u.x <= arena.ENEMY[2] + 1]
        SESSIONS.close(layout.handle)
        assert 3 * len(enemy) < len(units[arena.INVULNERABLE_ENEMY]) < 4 * len(enemy)  # 4 bases, two overlapping

        assert all(u.x < arena.SIZE and u.y < arena.SIZE for player in units for u in player)
        assert not [u for u in units[0] if u.unit_const in (1063, 1347)]  # no trees
    finally:
        SESSIONS.close(o.handle)
