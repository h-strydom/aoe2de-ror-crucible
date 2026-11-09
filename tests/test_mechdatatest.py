"""The mechanics test, part 2: the data mod carries the copied tasks and techs; the scenario builds."""
from __future__ import annotations

import json
import struct

from genieutils.datfile import DatFile

from aoe2ed import xs
from aoe2ed.session import SESSIONS
from crucible import mechdatatest as md
from crucible import testmod as tm


def test_data_mod_mechanics(tmp_path):
    folder = tm.build_data_mod(tmp_path)
    d = DatFile.parse(str(folder / tm.ROR_DAT / "empires2_x2_p1.dat"))
    u = d.civs[2].units
    tasks = lambda uid, act: [t for t in u[uid].bird.tasks if t.action_type == act]
    assert {t.search_wait_time for t in tasks(tm.HOPLITE, tm.AURA)} == set(tm.PHALANX)
    assert tasks(tm.TOWN_CENTER, tm.AURA)[0].class_id == tm.INFANTRY
    assert tasks(tm.AXEMAN, tm.LOOT)
    assert tasks(tm.SHORT_SWORDSMAN, tm.HP_TRANSFORM)[0].work_value_1 == tm.LONG_SWORDSMAN
    assert tasks(tm.CLUBMAN, tm.EXTRA_SPAWN)[0].work_value_1 == tm.CLUBMAN
    mule = tm.ported_ids()[tm.MULE_CART]
    assert mule in u[123].bird.drop_sites                                    # a lumberjack may drop at it
    sites = json.loads((folder / tm.ROR_DAT / "dropsites.json").read_text(encoding="utf-8"))["drop_site_list"]
    assert any(e["building_id"] == mule for e in sites)
    types = {d.effects[d.techs[t].effect_id].effect_commands[0].type for t in tm.wonder_extra_tech_ids()}
    assert types == {7, 25, 11}


def test_scenario_and_report(tmp_path):
    path = md.build(tmp_path)
    o = SESSIONS.open(path)
    SESSIONS.close(o.handle)
    assert xs.check(md.xs_code(1))["ok"]
    vals = [md.MAGIC, md.VERSION, md.TAG_SAMPLE, 5, 1, 2, 3, 4, 500, 1, 2, 0, 3, 999]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    assert "999" in md.report(record)
