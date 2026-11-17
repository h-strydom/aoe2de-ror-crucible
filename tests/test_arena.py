from aoe2ed.session import SESSIONS

from crucible.scenarios import arena


def test_arena_opens_as_a_ror_scenario():
    o = SESSIONS.open(arena.ARENA)

    try:
        assert o.scenario.sections["FileHeader"].unknown_numbers == [11]  # RoR's data set, or the game won't load it
        assert o.scenario.map_manager.map_size == 220
    finally:
        SESSIONS.close(o.handle)
