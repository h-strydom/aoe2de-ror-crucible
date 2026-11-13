from aoe2ed.session import SESSIONS

from crucible.scenarios import ground, parts


def test_ground_is_even_mud_and_keeps_the_units(tmp_path):
    o = SESSIONS.open(ground.build(tmp_path))
    edited = SESSIONS.open(parts.EDITED)

    try:
        tiles = o.scenario.map_manager.terrain
        assert {(t.terrain_id, t.elevation) for t in tiles} == {(parts.MUD, ground.ELEVATION)}
        assert o.scenario.sections["FileHeader"].unknown_numbers == [11]

        def count(s):
            return [len(player) for player in s.unit_manager.units]

        assert count(o.scenario) == count(edited.scenario)
    finally:
        SESSIONS.close(o.handle)
        SESSIONS.close(edited.handle)
