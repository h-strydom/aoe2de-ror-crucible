"""The ruins and artifacts test scenario builds and its XS checks clean."""
from __future__ import annotations

from aoe2ed import triggers as T
from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import ruinstest as rt
from crucible.testmod import ruin_monument_id


def test_build(tmp_path):
    rm = ruin_monument_id()
    assert xs.check(rt.xs_code(rm))["ok"]
    path = rt.build(tmp_path)
    o = SESSIONS.open(path)
    try:
        s = o.scenario
        setup = T.trigger_to_dict(next(t for t in s.trigger_manager.triggers if t.name == "Setup"))
        trickles = [e for e in setup["effects"] if e.get("tribute_list") in rt.MONUMENT_TRICKLES]
        assert len(trickles) == 12                                    # four trickles for players 1-3
        owned = {p: [u.unit_const for u in s.unit_manager.units[p]] for p in (0, 2, 3, 4, 5)}
        assert rm in owned[2] and rt.MONUMENT in owned[3] and rt.RUINS in owned[4] and rt.RUINS in owned[5]
        assert rm in owned[0] and rt.RUINS in owned[0]                # Gaia objects for player 1 to capture
        assert sum(u.unit_const == rt.ARTIFACT for u in s.unit_manager.units[1]) == 2
    finally:
        SESSIONS.close(o.handle)
