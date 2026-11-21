from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import meta
from crucible.scenarios import bases, run, waves


def test_run_hands_the_base_to_the_allies(tmp_path, techs):
    o = SESSIONS.open(run.build(tmp_path, techs))

    try:
        s = o.scenario
        units = s.unit_manager.units
        keeps = [u.unit_const for u in units[run.Faction.PLAYER] if u.unit_const in run.KEEPS]
        villagers = [u for u in units[run.Faction.PLAYER] if u.unit_const in (run.VILLAGER_MALE, run.VILLAGER_FEMALE)]
        assert sorted(keeps) == sorted(run.KEEPS)
        assert len(villagers) == 4
        assert s.player_manager.players[run.Faction.PLAYER].food == 200
        assert len(units[run.Faction.ALLIES]) > 100
        assert s.player_manager.active_players == 5
        assert s.sections["FileHeader"].unknown_numbers == [11]
        names = {t.name for t in s.trigger_manager.triggers}
        assert {"Wonder lost", "Shared vision", "Full vision", "Wave: Capital walk in"} <= names
        assert "Wave: City States sent" in names
        assert {"Wave: timer (Hard)", "Lane: Capital west is Legion"} <= names
        assert {"Meta: load currency", "Meta: bank currency"} <= names  # each wave pays its age's resource
        bank = next(t for t in s.trigger_manager.triggers if t.name == "Meta: bank currency")
        assert {e.message for e in bank.effects if e.message} == set(meta.CURRENCY)
        assert not any(n.startswith("Legion: ") for n in names)  # the XS researches the Legion's techs itself
        assert {"Meta: load upgrades", "Meta: villager 6", "Meta: House 5", "Meta: kept buildings to age 3"} <= names
        assert {"Meta: starting building 70 2", "Allies: camp buildings cleared"} <= names
        assert any(u.unit_const == run.KEEPER for u in units[run.Faction.ALLIES])
        assert {"Meta: Clubmen", "No hub buttons", "No data mod", "No data mod: defeat"} <= names
        assert {"Player: no walls or gates", "Win: claim victory offered", "Win: claim victory"} <= names
        cleared = next(t for t in s.trigger_manager.triggers if t.name == "Allies: camp buildings cleared")
        assert cleared.effects and all(e.effect_type == 14 for e in cleared.effects)  # killed: rubble, not removed
        assert {f"Base: {name}" for name, _ in bases.BASES} <= names  # an optional objective per Legion base
        assert {"Allies: age 3", "Meta: Granary 1 placed"} <= names
        assert any(n.startswith("Boon: ") for n in names)

        messages = [e.message for t in s.trigger_manager.triggers for e in t.effects if e.message]
        code = "\n".join(m for m in messages if "{" in m)  # the scripts, not the timer's text
        assert "crucibleRunStart" in code and "crucibleWaves" in code and "crucibleShopOpen" in code
        result = xs.check(code)
        assert result["ok"], result["diagnostics"]
    finally:
        SESSIONS.close(o.handle)


def test_lanes_are_straight():
    for lane in (*waves.CAPITAL, *waves.CITY_STATES):
        spawn, stage, target = lane.spawn[1], lane.stage[1], lane.target[1]
        assert spawn[0] == stage[0] == target[0] or spawn[1] == stage[1] == target[1], lane.name


def test_lanes_spawn_short_of_staging():
    for lane in waves.LANES:
        sx1, sy1, sx2, sy2 = lane.spawned
        tx1, ty1, tx2, ty2 = lane.staged
        assert sx2 < tx1 or tx2 < sx1 or sy2 < ty1 or ty2 < sy1, lane.name  # a send never takes a new wave


def test_spawn_rows_short_of_staging():
    for lane in waves.LANES:
        sx1, sy1, sx2, sy2 = lane.spawn_rows
        tx1, ty1, tx2, ty2 = lane.staged
        assert sx2 < tx1 or tx2 < sx1 or sy2 < ty1 or ty2 < sy1, lane.name  # a unit in its spawn rows isn't staged


def test_walls_start_damaged_never_destroyed():
    from crucible.scenarios import run_xs

    assert sum(chance for chance, _, _ in run_xs.WALL_STATES) == 100
    assert all(low > 0 for _, low, _ in run_xs.WALL_STATES)
    assert "crucibleRunTowers" not in run_xs.start({72: 200}, [], allies=5, player=1, invulnerable=2)
