from aoe2ed.session import SESSIONS

from crucible.scenarios import parts


def test_each_part_on_its_own_small_map(tmp_path):
    sizes = {}

    for path in parts.build(tmp_path):
        o = SESSIONS.open(path)

        try:
            s = o.scenario
            buildings = [u for player in s.unit_manager.units for u in player]
            side = s.map_manager.map_size
            sizes[path.stem] = side
            assert buildings and all(0 < u.x < side and 0 < u.y < side for u in buildings)
            assert {t.terrain_id for t in s.map_manager.terrain} == {parts.MUD}
            assert s.sections["FileHeader"].unknown_numbers == [11]

            if path.stem.endswith("north"):
                assert min(u.y for u in buildings) == 0.5  # against the top edge
        finally:
            SESSIONS.close(o.handle)

    assert sizes["crucible_part_west"] == sizes["crucible_part_east"] < sizes["crucible_part_north"]
