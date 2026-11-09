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
    assert tasks(tm.AXEMAN, tm.EXTRA_SPAWN)[0].work_value_1 == tm.AXEMAN
    assert {st.type: st.amount for st in u[tm.SCOUT].resource_storages if st.type in tm.HALF_POP_STORAGES}         == tm.HALF_POP_STORAGES
    ids = tm.ported_ids()
    assert u[ids[2110]].bird and ids[2110] in {t.unit_id for t in u[ids[2110]].bird.tasks if t.action_type == tm.AURA}
    assert all(src in ids for src in tm.PORTED_WHOLE)
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
    assert xs.check(md.xs_code(1, (2, 3), (2, 4, 3)))["ok"]
    vals = [md.MAGIC, md.VERSION, md.TAG_SAMPLE, 5, 1, 2, 3, 4, 500, 10, 20, *range(len(md.COUNTED)), 999, 7, 8, 9]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    assert "999" in md.report(record)


def _body(raw: bytes) -> bytes:
    import zlib
    for off in range(0, 6000):
        try:
            out = zlib.decompressobj(-15).decompress(raw[off:])
        except zlib.error:
            continue
        if len(out) > 10000:
            return out
    raise AssertionError("no compressed body found")


def test_half_pop_float_written(tmp_path):
    """AoE2ScenarioParser writes attribute 110 only to the integer field; the Horse Archer effect forces -0.5 into
    the float field (the Bowmen one is left as the parser writes it, for comparison)."""
    path = md.build(tmp_path)
    assert _body(path.read_bytes()).count(struct.pack("<f", -0.5)) >= 1
