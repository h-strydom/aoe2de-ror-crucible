"""The map tricks test: build blockers in the data mod, the scenario's triggers, the record."""
from __future__ import annotations

import struct

from genieutils.datfile import DatFile

from aoe2ed import xs
from aoe2ed.session import SESSIONS
from crucible import maptrickstest as mt
from crucible import testmod as tm


def test_blockers_in_data_mod(tmp_path):
    d = DatFile.parse(str(tm.build_data_mod(tmp_path) / tm.ROR_DAT / "empires2_x2_p1.dat"))
    ids = tm.blocker_ids()
    for name in tm.BLOCKERS:
        assert d.civs[0].units[ids[name]].can_be_built_on == 0
    assert d.civs[0].units[ids["invisible build blocker"]].standing_graphic == (-1, -1)


def test_scenario_and_report(tmp_path):
    path, tracked = mt.build(tmp_path)
    o = SESSIONS.open(path)
    try:
        s = o.scenario
        assert s.map_manager.get_tile(x=mt.STRIP_X[0], y=mt.STRIP_ROWS["Rock 1 layer"]).layer == mt.ROCK_1
        names = {t.name for t in s.trigger_manager.triggers}
        assert {"Safe zone A", "Enemy attack", "March", "Decisions", "Decision 3 option 2"} <= names
    finally:
        SESSIONS.close(o.handle)
    assert xs.check(mt.xs_code((1, 2, 3), 2, mt.ZONE_B, [t for _, t in tracked]))["ok"]
    vals = [mt.MAGIC, mt.VERSION, 1, 9, mt.TAG_SAMPLE, 5, 1000, 1000, 500, 120]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    out = mt.report(record, ["x"])
    assert "1000" in out and "120" in out
