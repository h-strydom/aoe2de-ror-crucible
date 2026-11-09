"""The mechanics test (part 1) builds, reads back, its XS checks clean, and its record decodes."""
from __future__ import annotations

import struct

from aoe2ed import triggers as T
from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import mechtest as mt


def test_build_reads_back(tmp_path):
    path, tracked = mt.build(tmp_path)
    assert xs.check(mt.xs_code([u for _, u in tracked]))["ok"]
    o = SESSIONS.open(path)                      # an attack value in `quantity` once made this unreadable
    try:
        settings = T.trigger_to_dict(next(t for t in o.scenario.trigger_manager.triggers
                                          if t.name == "Mechanics settings"))
        attrs = {e["object_attributes"] for e in settings["effects"] if e["type"] == "modify_object_attribute"}
        assert {mt.REGEN, mt.REFLECT, mt.AREA, mt.BONUS_RESIST, mt.ADD_ATTACK, mt.DEAD_UNIT, mt.CHARGE_TYPE} <= attrs
    finally:
        SESSIONS.close(o.handle)


def test_report_decodes(tmp_path):
    n = 2
    vals = [mt.MAGIC, mt.VERSION, n, 11, 12, mt.TAG_SAMPLE, 0, 0, 0, 60, 300, mt.TAG_SAMPLE, 2, 1, 1, 59, 290]
    record = tmp_path / "r.xsdat"
    record.write_bytes(struct.pack(f"<{len(vals)}i", *vals))
    out = mt.report(record, ["a", "b"])
    assert "290" in out and "your Bowmen" in out
