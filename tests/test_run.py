from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible.scenarios import run, waves


def test_run_hands_the_base_to_the_allies(tmp_path, techs):
    o = SESSIONS.open(run.build(tmp_path, techs))

    try:
        s = o.scenario
        units = s.unit_manager.units
        keeps = [u.unit_const for u in units[run.Faction.PLAYER] if u.unit_const in run.KEEPS]
        villagers = [u for u in units[run.Faction.PLAYER] if u.unit_const not in run.KEEPS]
        assert sorted(keeps) == sorted(run.KEEPS)
        assert len(villagers) == 4
        assert s.player_manager.players[run.Faction.PLAYER].food == 200
        assert len(units[run.Faction.ALLIES]) > 100
        assert s.player_manager.active_players == 5
        assert s.sections["FileHeader"].unknown_numbers == [11]
        names = {t.name for t in s.trigger_manager.triggers}
        assert {"Wonder lost", "Shared vision", "Full vision", "Wave: Capital walks in", "No shop yet"} <= names
        assert {"Meta: load upgrades", "Meta: villager 6", "Meta: House 7", "Meta: Barracks 1"} <= names
        assert "Meta: Clubmen" in names

        messages = [e.message for t in s.trigger_manager.triggers for e in t.effects if e.message]
        code = "\n".join(m for m in messages if "{" in m)  # the scripts, not the timer's text
        assert "crucibleRunStart" in code and "crucibleWaves" in code
        result = xs.check(code)
        assert result["ok"], result["diagnostics"]
    finally:
        SESSIONS.close(o.handle)


def test_lanes_are_straight():
    for lane in (*waves.CAPITAL, *waves.CITY_STATES):
        spawn, stage, target = lane.spawn[1], lane.stage[1], lane.target[1]
        assert spawn[0] == stage[0] == target[0] or spawn[1] == stage[1] == target[1], lane.name
