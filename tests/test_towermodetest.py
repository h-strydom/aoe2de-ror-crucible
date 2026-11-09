"""The tower modes test: the data mod's towers, the scenario, the record."""
from __future__ import annotations

import struct

from genieutils.datfile import DatFile

from aoe2ed import xs
from aoe2ed.session import SESSIONS
from crucible import testmod as tm
from crucible import towermodetest as tt


def test_towers_in_data_mod(tmp_path):
    d = DatFile.parse(str(tm.build_data_mod(tmp_path) / tm.ROR_DAT / "empires2_x2_p1.dat"))
    u = d.civs[2].units
    ids = tm.tower_mode_ids()
    assert u[ids["boulder"]].type_50.attacks[0].amount == tm.BOULDER_DAMAGE
    for label, event, target in tm.TOWER_CHARGES:
        tower, twin = u[ids[label]], u[ids[f"{label} (ballista)"]]
        assert tower.type_50.min_range == tm.TOWER_MIN_RANGE
        assert (tower.creatable.charge_type, tower.creatable.charge_event, tower.creatable.charge_target) == \
            (6, event, target)
        assert (tower.nothing, twin.nothing, tower.trait, twin.trait) == (twin.id, tower.id, 8, 8)


def test_scenario_and_report(tmp_path):
    path, tracked = tt.build(tmp_path)
    o = SESSIONS.open(path)
    SESSIONS.close(o.handle)
    assert len(tracked) == 12 and xs.check(tt.xs_code([t for _, t in tracked]))["ok"]
    vals = [tt.MAGIC, tt.VERSION, 1, 9, tt.TAG_SAMPLE, 2, 37]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    assert "37" in tt.report(record, ["x"])
