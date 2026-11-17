from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible.scenarios import run


def test_run_hands_the_base_to_the_allies(tmp_path):
    o = SESSIONS.open(run.build(tmp_path))

    try:
        s = o.scenario
        units = s.unit_manager.units
        assert sorted(u.unit_const for u in units[run.Faction.PLAYER]) == sorted(run.KEEPS)
        assert len(units[run.Faction.ALLIES]) > 100
        assert s.player_manager.active_players == 5
        assert s.sections["FileHeader"].unknown_numbers == [11]
        assert "Wonder lost" in [t.name for t in s.trigger_manager.triggers]

        code = "\n".join(e.message for t in s.trigger_manager.triggers for e in t.effects if e.message)
        assert "crucibleRunStart" in code
        result = xs.check(code)
        assert result["ok"], result["diagnostics"]
    finally:
        SESSIONS.close(o.handle)
