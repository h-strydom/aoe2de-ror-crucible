from aoe2ed.session import SESSIONS

from crucible.scenarios import maps


def test_maps_open_as_ror_scenarios():
    for name in maps.MAPS:
        o = SESSIONS.open(maps.asset(name))

        try:
            assert o.scenario.sections["FileHeader"].unknown_numbers == [11], name  # or the game won't load it
        finally:
            SESSIONS.close(o.handle)
