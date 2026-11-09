"""The unit test: the data mod carries the fire modes and mercenaries; the scenario builds; the record decodes."""
from __future__ import annotations

import struct

from genieutils.datfile import DatFile

from aoe2ed import xs
from aoe2ed.session import SESSIONS
from crucible import testmod as tm
from crucible import unitfiretest as ut


def test_data_mod_unit_modes(tmp_path):
    d = DatFile.parse(str(tm.build_data_mod(tmp_path) / tm.ROR_DAT / "empires2_x2_p1.dat"))
    u = d.civs[2].units
    siege, merc = tm.unit_mode_ids()
    assert (u[tm.BOWMAN].trait, u[tm.BOWMAN].nothing) == (tm.SWITCH_TRAIT, siege)
    assert (u[siege].trait, u[siege].nothing) == (tm.SWITCH_TRAIT, tm.BOWMAN)
    assert (tm.BUILDING_ARMOUR, tm.SIEGE_BONUS) in {(a.class_, a.amount) for a in u[siege].type_50.attacks}
    assert u[tm.HORSE_ARCHER].creatable.total_projectiles == tm.KIPCHAK_ARROWS
    assert u[merc].creatable.resource_costs[0].type == tm.MERC_TOKEN
    gift = d.effects[d.techs[tm.mercenary_tech_id()].effect_id].effect_commands[0]
    assert (gift.type, gift.a, gift.d) == (11, tm.MERC_TOKEN, tm.MERC_GIFT)
    ids = tm.ported_ids()
    assert u[ids[tm.FIRE_ARCHER]].creatable.charge_type == 6


def test_scenario_and_report(tmp_path):
    path, tracked = ut.build(tmp_path)
    o = SESSIONS.open(path)
    SESSIONS.close(o.handle)
    assert xs.check(ut.xs_code([t for _, t in tracked], 1))["ok"]
    vals = [ut.MAGIC, ut.VERSION, 1, 7, ut.TAG_SAMPLE, 5, 1, 2, 3, 4, 0, 0, 0, 42]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    assert "42" in ut.report(record, ["x"])
