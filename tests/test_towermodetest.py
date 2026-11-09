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
    arrow, boulder = u[ids["arrow projectile"]], u[ids["boulder projectile"]]
    assert (arrow.type_50.min_range, arrow.type_50.max_range) == (tm.TOWER_MIN_RANGE, tm.TOWER_RANGE)
    assert boulder.type_50.attacks[0].amount == tm.BOULDER_DAMAGE
    for label, event, target, _, _, normal in tm.TOWER_STYLES:
        tower = u[ids[label]]
        cr = tower.creatable
        assert (cr.charge_type, cr.charge_event, cr.charge_target) == (6, event, target)
        charge = ids["arrow projectile" if normal == "boulder" else "boulder projectile"]
        assert tower.creatable.charge_projectile_unit == charge
    there, back = (d.techs[t] for t in tm.tower_mode_tech_ids())
    assert there.repeatable == back.repeatable == 1
    assert d.effects[there.effect_id].effect_commands[0].b == ids["ballista"]


def test_scenario_and_report(tmp_path):
    path, tracked = tt.build(tmp_path)
    o = SESSIONS.open(path)
    SESSIONS.close(o.handle)
    assert len(tracked) == 16 and xs.check(tt.xs_code([t for _, t in tracked]))["ok"]
    vals = [tt.MAGIC, tt.VERSION, 1, 9, tt.TAG_SAMPLE, 2, 37]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    assert "37" in tt.report(record, ["x"])
